/*
Run as part of Docker build for the test DB container. (Dockerfile_db_test)

This allows tests to modify the return of the builtin now function in postgres.
It points to a mock_now table with a single row and uses the default if null.
In JS tests the TimeWarp util, which controls mocking the current time, has a
syncDbNow function that is used to send the new mocked time to postgres.

The BA version of this contains a loop that updates column defaults to use the
overridden now function. However, if this script runs before the migrations,
which the Docker setup does, that loop is unneeded. So it is removed here.

Reading:
https://www.postgresql.org/message-id/1393426627566-5793703.post@n5.nabble.com
https://www.postgresql.org/docs/9.5/static/ddl-schemas.html
*/

-- This ensures created tables use public.now as their default value.
ALTER DATABASE "fastackstarter_test" SET search_path TO public,pg_catalog;

CREATE TABLE public.mock_now ("now" TIMESTAMP WITH TIME ZONE);
INSERT INTO public.mock_now ("now") VALUES (NULL);

CREATE OR REPLACE FUNCTION public.now()
RETURNS TIMESTAMP WITH TIME ZONE AS
'SELECT COALESCE(now, pg_catalog.now()) FROM public.mock_now;'
LANGUAGE SQL;
