# Fused documentation

**Fused - Connect Your APIs Once, Use Everywhere**

Bring internal, partner, and third-party APIs into Fused. Reuse integrations across projects, teams, and AI agents while staying in control of who can access what. This repository contains the public guides and references for Fused and Harnest, built with Mintlify.

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
