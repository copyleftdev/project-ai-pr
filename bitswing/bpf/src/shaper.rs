#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action::XDP_PASS,
    macros::{map, xdp},
    maps::HashMap,
    programs::XdpContext,
};
use core::mem;

#[repr(C)]
pub struct RateLimit {
    pub bps: u32,
}

#[map(name = "RATE_LIMIT_MAP")]
static mut RATE_LIMIT_MAP: HashMap<u16, RateLimit> = HashMap::with_max_entries(1024, 0);

#[xdp(name = "shaper")]
pub fn shaper(ctx: XdpContext) -> u32 {
    if try_shaper(&ctx).is_err() {
        XDP_PASS
    } else {
        XDP_PASS
    }
}

fn try_shaper(ctx: &XdpContext) -> Result<(), i64> {
    let data = ctx.data();
    let data_end = ctx.data_end();

    // Check length for at least an Ethernet header
    if data + mem::size_of::<aya_bpf::bindings::ethhdr>() > data_end {
        return Ok(());
    }

    // Hard-coded example: port = 80
    if let Some(limit) = unsafe { RATE_LIMIT_MAP.get(&80u16) } {
        let _bps = limit.bps;
        // Real shaping logic would track usage & drop/mark packets as needed
    }
    Ok(())
}
