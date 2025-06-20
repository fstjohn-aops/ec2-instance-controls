## What is this?

The tools directory contains executable scripts that are run from the command
line using commands like `npx tsx tools/sample.ts`.

## What does each file do?

Every file should give documentation without doing anything when run with
`--help`.

## What is it based on?

This directory and its conventions are heavily based off BA's scripts/
directory.

## How do I get started writing a new script?

Here is a starter:

```js
// Always-use dependencies. run provides a basic error handling and timeout
// setup. Yargs does documentation and argument parsing for CLI tools.
import run from "./util/run";
import Yargs from "yargs";
import {hideBin} from "yargs/helpers";

// Your dependencies and helpers here. Some common ones to start you off:
import _ from "lodash";
import * as Path from "path";

// Type for Yargs-parsed arguments. If you have no options, keep as-is.
type Args = {
};

async function main() {
  // Your command-line options go in this method chain. See the yargs docs.
  const argv: Args = Yargs(hideBin(process.argv))
    .strictOptions()
    .help()
    .version(false)
    .usage("Basic usage info here; multiple calls to usage are allowed")
    .argv;

  // Your code here.
}

run(main);
```

The [yargs documentation](https://github.com/yargs/yargs#usage-) is likely to
be useful.

[sample](./sample.ts) is a small example script to refer to.

## What should I know before writing scripts?

Familiarity with stdin/stdout/stderr and piping in unix-like environments is
useful, especially for deciding on good input and output formats.
[Here](http://www.learnlinux.org.za/courses/build/shell-scripting/ch01s04.html)
is an introduction.

Ask Palmer or other developers if you want more advice.

## What if I need to reuse logic from this folder outside a script?

Move the shared logic to a file in a util folder, whether `tools/util`
or some other suitable location like `src/util`, and have both the
script here and your code reusing it both require that util.

You could write the script in a way that makes them simultaneously runnable and
requirable. But this makes maintaining the script harder and more error-prone,
so avoid it.
