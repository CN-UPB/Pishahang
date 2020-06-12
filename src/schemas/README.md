# Pishahang JSON Schemas

This directory contains JSON schemas for many objects used in Pishahang, including descriptors and records.
All schemas are written in the YAML format and placed in the `lib` directory.
Schemas may contain references to other schema files.
Yet, many JSON schema implementations are not capable of resolving these references.
Hence, this directory also includes a Node.js script to resolve the references and write the resulting schemas to the `bundled` directory, in YAML and JSON formats.
When you make changes to schema files in the `lib` directory, make sure to follow the [bundling section](#bundling) to update the bundled files as well.

## Installation

In order to run the tests and bundle the schema files, [Node.js](https://nodejs.org/en/download/) >= 10 has to be installed on your machine.
With Node.js installed, run `npm install` to install the required dependencies into the `node_modules` directory.

## Bundling

`npm run bundle` resolves the JSON schema references and saves the resulting schemas to the `bundled` directory.

## Tests

In order to add tests to a schema, add a `[schema name]-tests` directory next to it that contains YAML files with data that should successfully validate against the schema.
The other way around, to assert that a certain YAML file is invalid, suffix it with `.invalid.yml`.
You can run the tests using `npm run test`.
