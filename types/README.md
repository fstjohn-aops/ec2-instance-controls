Publish TypeScript types and TypeBox validators. [TypeBox](https://github.com/sinclairzx81/typebox) is used for runtime type validation.

## Purpose

Sharing types and validators ensures consistency within a project and across projects. For example, published types can:

- Keep servers and clients aligned
- Help external projects write requests to and consume responses from your API

## Writing types

For sharing implementation-level types, write in `src/private.ts`. Import as needed within folders of this project. These exports will not be published.

Put TypeScript types in `src/types.ts`. The file will be passed to `typebox-codegen`, which outputs corresponding TypeBox validators and [Static<>](https://github.com/sinclairzx81/typebox?tab=readme-ov-file#example) TypeScript types into `src/validators-from-types.ts`. This means you can write TypeScript types and get TypeBox validators for free.

The codegen runs before publishing. Run manually if needed:

```bash
npm run generate
```

Put existing TypeBox objects in `src/validators.ts`. Avoid writing new ones if they can be generated from an equivalent TypeScript type in `src/types.ts`.

## Testing

[Jest](https://jestjs.io/) runs tests in `/test` of the name `*.test.ts`.

```bash
npm run test
```

For continuous changes, try:

```bash
npm run test-watch
```

`codegen.test.ts` confirms generation is working. If you do not have schemas to generate from `types.ts`, [skip the test](https://jestjs.io/docs/api#describeskipname-fn).

`example.test.ts` demonstrates testing the behavior and shape of a published schema. This is vital for ensuring the expected shape across changes.

For the sake of the consumers of published types, write many tests. This stores the intent of your types and schemas.

## Publishing

Before publishing:

- Install [Trove](https://github.com/aops-ba/trove/tree/main?tab=readme-ov-file#aops-trove)
- Update `name` in `package.json` to be the project name followed by `-types`
- `export` shared types and objects from `types.ts` and `validators.ts`

Publishing will share everything exported from `src/validators.ts` and the generated `src/validators-from-types.ts`. To publish:

```bash
npm run publish-trove
```

## Usage

1. Authenticate via Trove

```bash
trove configure-codeartifact
```

2. Install the package

```bash
npm i @aops-trove/project-name-here-types
```

3. Import TypeScript types or TypeBox validators

```ts
import {requestT, responseT} from "@aops-trove/project-name-here-types";
```

## Compatibility

Ensuring compatibility is crucial when publishing shared types for your package. Compatibility ensures that changes to the types do not break existing functionality for users of your API. This section outlines our approach to achieving backwards and forwards compatibility.

- **Minimize breaking changes**: See if there is another way to accomplish the change without breaking support
- **Schema Evolution**: Types support schema evolution to allow changes without breaking clients
- **Backwards Compatibility**: Older clients can communicate with newer API versions
- **Forwards Compatibility**: Newer clients work with older API versions

To learn more, read [the chapter on encoding from Designing Data Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch04.html).

### API Versioning

Managing API versioning is the publisher's responsibility.

- **Header-based Versioning**: Clients specify the API version using a header
- **URL-based Versioning**: Different versions accessed via distinct URLs, e.g. `/v1/api` and `/v2/api`

If you make a breaking change, consider still supporting the older version of your API while clients migrate to your new types.
