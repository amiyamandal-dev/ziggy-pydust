// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const std = @import("std");
const mem = std.mem;
const Allocator = std.mem.Allocator;
const ffi = @import("ffi");
const py = @import("./pydust.zig");

pub const PyMemAllocator = struct {
    const Self = @This();

    pub fn allocator(self: *const Self) Allocator {
        return .{
            .ptr = @constCast(self),
            .vtable = &.{
                .alloc = alloc,
                .remap = remap,
                .resize = resize,
                .free = free,
            },
        };
    }

    fn alloc(ctx: *anyopaque, len: usize, ptr_align: mem.Alignment, ret_addr: usize) ?[*]u8 {
        // As per this issue, we will hack an aligned allocator.
        // https://bugs.python.org/msg232221
        _ = ret_addr;
        _ = ctx;

        // FIXME(ngates): we should have a separate allocator for re-entrant cases like this
        // that require the GIL, without always paying the cost of acquiring it.
        const gil = py.gil();
        defer gil.release();

        const alignment_bytes = ptr_align.toByteUnits();

        // Safety check: ensure alignment fits in u8 for our header scheme
        // For alignments > 255, we need a different approach
        if (alignment_bytes > 255) {
            // For large alignments, fall back to over-allocating
            // and storing a u16 offset instead
            std.debug.print("Warning: Large alignment {d} requested, may be inefficient\n", .{alignment_bytes});
            return null; // TODO: Implement large alignment support
        }

        const alignment: u8 = @intCast(alignment_bytes);

        // By default, ptr_align == 1 which gives us our 1 byte header to store the alignment shift
        // We need to allocate enough space for alignment + our header
        const raw_ptr: usize = @intFromPtr(ffi.PyMem_Malloc(len + alignment) orelse return null);

        // Calculate the alignment offset needed
        const misalignment = raw_ptr % alignment_bytes;
        const shift: u8 = if (misalignment == 0) alignment else @intCast(alignment_bytes - misalignment);
        std.debug.assert(0 < shift and shift <= alignment);

        const aligned_ptr: usize = raw_ptr + shift;

        // Verify we're not writing outside our allocated region
        std.debug.assert(aligned_ptr > raw_ptr); // Ensure we moved forward
        std.debug.assert(aligned_ptr - 1 >= raw_ptr); // Ensure header byte is in our allocation

        // Store the shift in the first byte before the aligned ptr
        // We know from above that we are guaranteed to own that byte.
        @as(*u8, @ptrFromInt(aligned_ptr - 1)).* = shift;

        return @ptrFromInt(aligned_ptr);
    }

    fn remap(ctx: *anyopaque, memory: []u8, ptr_align: mem.Alignment, new_len: usize, ret_addr: usize) ?[*]u8 {
        // As per this issue, we will hack an aligned allocator.
        // https://bugs.python.org/msg232221
        _ = ret_addr;
        _ = ctx;

        // FIXME(ngates): we should have a separate allocator for re-entrant cases like this
        // that require the GIL, without always paying the cost of acquiring it.
        const gil = py.gil();
        defer gil.release();

        const alignment_bytes = ptr_align.toByteUnits();

        // Safety check: ensure alignment fits in u8
        if (alignment_bytes > 255) {
            std.debug.print("Warning: Large alignment {d} requested in remap\n", .{alignment_bytes});
            return null;
        }

        const alignment: u8 = @intCast(alignment_bytes);

        // get shift - verify it's within reasonable bounds
        const old_shift = @as(*u8, @ptrFromInt(@intFromPtr(memory.ptr) - 1)).*;
        if (old_shift > alignment) {
            // Corrupted header or mismatched alignment
            return null;
        }

        const origin_mem_ptr: *anyopaque = @ptrFromInt(@intFromPtr(memory.ptr) - old_shift);

        // By default, ptr_align == 1 which gives us our 1 byte header to store the alignment shift
        const raw_ptr: usize = @intFromPtr(ffi.PyMem_Realloc(origin_mem_ptr, new_len + alignment) orelse return null);

        // Calculate the alignment offset needed
        const misalignment = raw_ptr % alignment_bytes;
        const shift: u8 = if (misalignment == 0) alignment else @intCast(alignment_bytes - misalignment);
        std.debug.assert(0 < shift and shift <= alignment);

        const aligned_ptr: usize = raw_ptr + shift;

        // Verify we're not writing outside our allocated region
        std.debug.assert(aligned_ptr > raw_ptr);
        std.debug.assert(aligned_ptr - 1 >= raw_ptr);

        // Store the shift in the first byte before the aligned ptr
        // We know from above that we are guaranteed to own that byte.
        @as(*u8, @ptrFromInt(aligned_ptr - 1)).* = shift;

        return @ptrFromInt(aligned_ptr);
    }

    fn resize(ctx: *anyopaque, buf: []u8, buf_align: mem.Alignment, new_len: usize, ret_addr: usize) bool {
        _ = ret_addr;
        _ = buf_align;
        _ = ctx;

        // Resize can succeed in two cases:
        // 1. Shrinking: new_len <= buf.len - we can always "shrink" without doing anything
        //    PyMem will keep track of the actual allocation size for us
        // 2. Growing within allocated space: This would require tracking the original allocation size,
        //    which we don't currently do.

        // For shrinking, we can succeed without any actual work
        if (new_len <= buf.len) {
            return true;
        }

        // For growing, we cannot resize in place since:
        // a) PyMem_Realloc can move the allocation, but we can't return the new pointer
        // b) We don't track the original allocation size to know if there's room
        // So we must return false to force the caller to allocate new memory
        return false;
    }

    fn free(ctx: *anyopaque, buf: []u8, buf_align: mem.Alignment, ret_addr: usize) void {
        _ = buf_align;
        _ = ctx;
        _ = ret_addr;

        const gil = py.gil();
        defer gil.release();

        // Fetch the alignment shift. We could check it matches the buf_align, but it's a bit annoying.
        const aligned_ptr: usize = @intFromPtr(buf.ptr);
        const shift = @as(*const u8, @ptrFromInt(aligned_ptr - 1)).*;

        const raw_ptr: *anyopaque = @ptrFromInt(aligned_ptr - shift);
        ffi.PyMem_Free(raw_ptr);
    }
}{};
