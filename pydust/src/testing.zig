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
const py = @import("./pydust.zig");

/// Test allocator with leak detection support
/// This wraps Zig's GeneralPurposeAllocator to track allocations
/// and report memory leaks to the pytest harness.
pub const TestAllocator = struct {
    gpa: std.heap.GeneralPurposeAllocator(.{
        .safety = true,
        .thread_safe = true,
        .verbose_log = false,
    }),
    leak_count: usize,

    const Self = @This();

    pub fn init() Self {
        return .{
            .gpa = .{},
            .leak_count = 0,
        };
    }

    pub fn allocator(self: *Self) std.mem.Allocator {
        return self.gpa.allocator();
    }

    /// Check for leaks and return true if any were detected
    pub fn deinit(self: *Self) bool {
        const leaked = self.gpa.deinit();
        if (leaked == .leak) {
            self.leak_count = self.gpa.total_requested_bytes;
            return true;
        }
        return false;
    }

    /// Get detailed leak information
    pub fn getLeakInfo(self: *const Self) LeakInfo {
        return .{
            .has_leak = self.leak_count > 0,
            .bytes_leaked = self.leak_count,
        };
    }
};

pub const LeakInfo = struct {
    has_leak: bool,
    bytes_leaked: usize,
};

/// Fixture for testing with automatic leak detection
/// Usage in tests:
/// ```zig
/// test "my test" {
///     var fixture = py.testing.TestFixture.init();
///     defer fixture.deinit();
///
///     const alloc = fixture.allocator();
///     // Your test code here
/// }
/// ```
pub const TestFixture = struct {
    test_allocator: TestAllocator,
    python_initialized: bool,

    const Self = @This();

    pub fn init() Self {
        return .{
            .test_allocator = TestAllocator.init(),
            .python_initialized = false,
        };
    }

    pub fn allocator(self: *Self) std.mem.Allocator {
        return self.test_allocator.allocator();
    }

    /// Initialize Python interpreter for the test
    pub fn initPython(self: *Self) void {
        if (!self.python_initialized) {
            py.initialize();
            self.python_initialized = true;
        }
    }

    pub fn deinit(self: *Self) void {
        if (self.python_initialized) {
            py.finalize();
        }

        if (self.test_allocator.deinit()) {
            const info = self.test_allocator.getLeakInfo();
            std.debug.print("\n⚠️  Memory leak detected: {} bytes leaked\n", .{info.bytes_leaked});
            @panic("Memory leak detected in test");
        }
    }
};

/// Helper to assert no leaks in a test block
pub fn expectNoLeaks(allocator: std.mem.Allocator) !void {
    // Get the underlying GPA if this is a TestAllocator
    _ = allocator; // For now, this is a placeholder
    // TODO: Implement leak checking
}
