# Fused documentation

**Fused — The simplification of integration.**

Build and deliver integrations faster, from a single service call to complex workflows for your applications and agents. This repository contains the public guides and references for Fused and Harnest, built with Mintlify.

[Documentation](https://usefused.com/docs) · [Website](https://usefused.com)

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview your documentation changes locally. To install, use the following command:

```
npm i -g mint
```

Run the following command at the root of your documentation, where your `docs.json` is located:

```
mint dev
```

View your local preview at `http://localhost:3000`.

## Validate changes

```bash
mint validate
mint broken-links
```

## Publishing changes

The connected Mintlify deployment publishes changes pushed to the default branch.
