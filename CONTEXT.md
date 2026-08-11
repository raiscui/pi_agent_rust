# Pi Agent Rust Context

本文件定义 Pi Agent Rust 的稳定命名边界,避免产品名、library crate 和用户命令混用。

## Language

**rpi CLI**:
Pi Agent Rust 对用户发布的唯一可执行命令。Cargo shipping binary、安装器、发布包和运行文档均使用 `rpi`。
_Avoid_: pi binary, pi-rust

**Pi**:
本项目的产品名称。
_Avoid_: rpi product

**pi library crate**:
Pi Agent Rust 的 Rust library crate 名称,供内部代码和 SDK 消费者引用,不对应用户 shell 命令。
_Avoid_: rpi crate
