# Ship the CLI as rpi

Pi Agent Rust ships its sole user-facing executable as `rpi`. This avoids collision with the separately installed pnpm `pi` command while preserving `Pi` as the product name and `pi` as the Rust library crate.
