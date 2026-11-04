# tidyjson

tidyjson is a powerful, lightweight CLI tool that seamlessly formats and validates JSON files. Whether you're a seasoned developer or just getting started, tidyjson empowers you to leverage clean, consistent JSON across your entire codebase.

## Features

- **Blazing fast** — formats a 10 MB file in milliseconds.
- **Robust validation** — catches errors before they reach production.
- **Flexible configuration** — tailor the output to your needs.

## Installation

It's worth noting that tidyjson requires Python 3.9 or later. Simply run:

```bash
pip install tidyjson
```

## Usage

Let's dive into how to use tidyjson. To format a file in place:

```bash
tidyjson --write config.json
```

To check a file without changing it, use `--check`. This exits with code 1 if the file isn't formatted, which makes it a great fit for CI pipelines.

## Contributing

We welcome contributions of all kinds! Whether it's fixing a bug, improving the docs, or adding a feature, every contribution is valued. In summary, tidyjson is a game-changer for anyone who works with JSON. Happy formatting!
