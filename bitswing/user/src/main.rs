use aya::{Bpf, include_bytes_aligned, maps::HashMap, programs::Xdp};
use aya::programs::xdp::XdpFlags;
use serde::Deserialize;
use std::fs;

#[derive(Deserialize)]
struct General {
    interface: String,
    default_rate_limit_bps: u32,
}

#[derive(Deserialize)]
struct Rule {
    port: u16,
    rate_limit_bps: u32,
}

#[derive(Deserialize)]
struct Config {
    general: General,
    rules: Vec<Rule>,
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct RateLimit {
    pub bps: u32,
}

static BPF_BYTES: &[u8] = include_bytes_aligned!(concat!(env!("OUT_DIR"), "/bitswing-bpf"));

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Read TOML config
    let config_str = fs::read_to_string("Config.toml")?;
    let config: Config = toml::from_str(&config_str)?;

    // Load BPF bytecode
    let mut bpf = Bpf::load(BPF_BYTES)?;
    let mut shaper = bpf.program_mut("shaper").ok_or("program not found")?;
    shaper.load()?;
    if let Some(xdp) = shaper.try_into_xdp() {
        xdp.attach(&config.general.interface, XdpFlags::SKB_MODE)?;
    }

    // Populate BPF map
    let mut rate_map = HashMap::<u16, RateLimit>::try_from(bpf.map_mut("RATE_LIMIT_MAP")?)?;
    let default_limit = RateLimit {
        bps: config.general.default_rate_limit_bps,
    };
    // Use port=0 as a "catch-all" or fallback
    rate_map.insert(&0, &default_limit, 0)?;

    // Insert per-port rules
    for rule in &config.rules {
        let limit = RateLimit { bps: rule.rate_limit_bps };
        rate_map.insert(&rule.port, &limit, 0)?;
    }

    println!(
        "BitSwing running on {}. Press Ctrl+C to stop.",
        config.general.interface
    );
    loop {
        std::thread::park();
    }
}
