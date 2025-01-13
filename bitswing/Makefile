# Makefile for BitSwing

# Project directories
BPF_DIR        := bpf
USER_DIR       := user

# BPF build output (assuming a release build)
BPF_TARGET     := $(BPF_DIR)/target/bpfel-unknown-none/release/bitswing-bpf

# User-space binary (release build)
USER_TARGET    := $(USER_DIR)/target/release/bitswing-user

# If you need a special Docker image to cross-compile eBPF, set it here:
AYA_BUILDER_IMAGE := ghcr.io/aya-rs/aya-builder-x86_64-unknown-linux-gnu:latest

# Phony targets don't correspond to actual files
.PHONY: all bpf user clean run install

## Default target: build everything
all: bpf user

## Build the BPF crate
bpf:
	# Option 1: Native build (requires rustup target add bpfel-unknown-none)
	# cd $(BPF_DIR) && cargo build --release --target bpfel-unknown-none
	#
	# Option 2: Use Docker-based builder (uncomment if you use aya-builder)
	# docker run --rm -v $(shell pwd):/workdir -w /workdir/$(BPF_DIR) \
	#     $(AYA_BUILDER_IMAGE) cargo build --release --target bpfel-unknown-none
	#
	# For now, we'll assume local native build:
	cd $(BPF_DIR) && cargo build --release --target bpfel-unknown-none

## Build the user-space crate
user:
	cd $(USER_DIR) && cargo build --release

## Clean all build artifacts
clean:
	cd $(BPF_DIR) && cargo clean
	cd $(USER_DIR) && cargo clean

## Run the user-space binary (requires sudo if attaching XDP)
run: all
	@echo "Running BitSwing user-space daemon..."
	sudo $(USER_TARGET)

## Optional: Install the user binary (and optionally the BPF bytecode) to /usr/local/bin
install: all
	@echo "Installing user binary to /usr/local/bin..."
	sudo cp $(USER_TARGET) /usr/local/bin/bitswing
	@echo "Installing BPF bytecode to /usr/local/lib/bitswing/..."
	sudo mkdir -p /usr/local/lib/bitswing
	sudo cp $(BPF_TARGET) /usr/local/lib/bitswing/bitswing-bpf
	@echo "Install complete."
