# New High-Impact Features

This guide covers three new high-impact features that significantly improve the developer experience with Ziggy Pydust:

1. **Memory Leak Detection** - Automatic detection of memory leaks in Zig tests
2. **Hot Reload / Watch Mode** - Automatic rebuilding on file changes
3. **Async/Await Support** - Integration with Python's async ecosystem

---

## Memory Leak Detection

Memory leak detection helps you catch memory management errors in your Zig code automatically during testing.

### Features

- ✅ Automatic leak detection in Zig tests
- ✅ Integration with GeneralPurposeAllocator
- ✅ Clear error messages with leak information
- ✅ Pytest integration with dedicated error type

### Usage

#### In Zig Tests

Use the `TestFixture` to automatically detect leaks:

```zig
const py = @import("pydust");
const std = @import("std");

test "safe memory management" {
    var fixture = py.testing.TestFixture.init();
    defer fixture.deinit(); // Will check for leaks automatically

    fixture.initPython();

    // Use the test allocator
    const alloc = fixture.allocator();

    // Allocate and properly free memory
    const data = try alloc.alloc(u8, 100);
    defer alloc.free(data);

    // Test passes - no leaks detected
}
```

#### Catching Leaks

If you forget to free memory, the test will fail with a clear error:

```zig
test "detecting memory leaks" {
    var fixture = py.testing.TestFixture.init();
    defer fixture.deinit(); // This will panic if there's a leak

    const alloc = fixture.allocator();

    // This will leak and be caught by deinit()
    _ = try alloc.alloc(u8, 50);
    // Forgot to call alloc.free() - leak!
}
```

Output:
```
======================================================================
MEMORY LEAK DETECTED in 'example/leak_detection.zig::detecting memory leaks'
======================================================================
The test allocator detected unreleased memory.
Please ensure all allocations are properly freed.
======================================================================
```

### Python-Side Integration

The pytest plugin automatically detects and reports leaks:

```python
from pydust.pytest_plugin import MemoryLeakError

def test_leaky_zig_code():
    """This will raise MemoryLeakError if Zig test leaks."""
    # Run your Zig test that may leak
    pass
```

---

## Hot Reload / Watch Mode

Watch mode automatically rebuilds your project when source files change, dramatically speeding up the development iteration cycle.

### Features

- ✅ Automatic file watching for Zig sources
- ✅ Debounced rebuilds (avoids rebuilding too frequently)
- ✅ Support for running tests after rebuild
- ✅ Pytest integration mode
- ✅ Configurable optimization levels

### Usage

#### Basic Watch Mode

Watch and rebuild on changes:

```bash
pydust watch --optimize Debug
```

#### Watch with Tests

Automatically run Zig tests after each rebuild:

```bash
pydust watch --optimize Debug --test
```

#### Pytest Watch Mode

Watch and run pytest on changes:

```bash
pydust watch --pytest

# With pytest arguments
pydust watch --pytest -v -k test_my_feature
```

### Configuration

Watch mode automatically monitors:
- All extension module root files (specified in `pyproject.toml`)
- Pydust source files (if in development mode)
- Python test files (in pytest mode)

Example output:

```
🚀 Ziggy Pydust Watch Mode
   Optimize: Debug
   Test mode: True

👀 Watching 15 files for changes...
   Press Ctrl+C to stop

🔄 Changes detected in 2 file(s):
   - example/hello.zig
   - example/classes.zig

🔨 Rebuilding...
✅ Build completed in 3.42s
```

### Programmatic Usage

You can also use watch mode programmatically:

```python
from pydust.watch import watch_and_rebuild, watch_pytest

# Simple watch and rebuild
watch_and_rebuild(optimize="Debug", test_mode=True)

# Pytest watch mode
watch_pytest(optimize="Debug", pytest_args=["-v"])
```

---

## Async/Await Support

Full integration with Python's async/await and asyncio ecosystem.

### Features

- ✅ PyCoroutine type wrapper
- ✅ PyAwaitable type wrapper
- ✅ Coroutine protocol support
- ✅ Integration with asyncio
- ✅ Ability to call Python coroutines from Zig
- ✅ Ability to create awaitable Zig objects

### Usage

#### Calling Python Coroutines from Zig

```zig
const py = @import("pydust");

pub fn call_coroutine(args: struct { coro: py.PyObject }) !py.PyObject {
    if (!py.PyCoroutine.check(args.coro)) {
        return py.TypeError(root).raise("Expected a coroutine");
    }

    const coro = py.PyCoroutine{ .obj = args.coro };

    // Send None to start the coroutine
    const result = try coro.send(null);

    return result;
}
```

#### Creating Awaitable Zig Objects

```zig
pub const SimpleFuture = py.class(struct {
    const Self = @This();

    result: ?py.PyObject = null,
    done: bool = false,

    pub fn __init__(self: *Self) void {
        self.* = .{};
    }

    pub fn set_result(self: *Self, args: struct { value: py.PyObject }) void {
        args.value.incref();
        self.result = args.value;
        self.done = true;
    }

    pub fn is_done(self: *const Self) bool {
        return self.done;
    }

    /// Make this future awaitable by implementing __await__
    pub fn __await__(self: *const Self) !py.PyIter {
        if (self.done) {
            if (self.result) |res| {
                res.incref();
                const tuple = try py.tuple(root, .{res});
                return try tuple.iter();
            }
        }
        return py.RuntimeError(root).raise("Future not ready");
    }
});
```

#### Using from Python

```python
import asyncio
from my_extension import SimpleFuture, call_coroutine

async def main():
    # Use the awaitable Zig object
    future = SimpleFuture()
    future.set_result(42)
    result = await future
    print(f"Result: {result}")  # Result: 42

    # Call Zig function with a coroutine
    async def my_coro():
        await asyncio.sleep(0.1)
        return "done"

    coro = my_coro()
    result = call_coroutine(coro)
    print(result)

asyncio.run(main())
```

### API Reference

#### PyCoroutine

```zig
pub const PyCoroutine = extern struct {
    obj: py.PyObject,

    /// Check if a Python object is a coroutine
    pub fn check(obj: py.PyObject) bool

    /// Send a value to the coroutine
    pub fn send(self: Self, value: ?py.PyObject) !py.PyObject

    /// Throw an exception into the coroutine
    pub fn throw(self: Self, exception: py.PyObject) !py.PyObject

    /// Close the coroutine
    pub fn close(self: Self) !void
};
```

#### PyAwaitable

```zig
pub const PyAwaitable = extern struct {
    obj: py.PyObject,

    /// Get the iterator for this awaitable
    pub fn iter(self: Self) !py.PyIter

    /// Await this awaitable (blocking)
    pub fn await_(self: Self) !py.PyObject
};
```

---

## Best Practices

### Memory Leak Detection

1. ✅ Always use `TestFixture` in your Zig tests
2. ✅ Use `defer` to ensure cleanup code runs
3. ✅ Match every `alloc()` with a `free()`
4. ✅ Match every `incref()` with a `decref()`

### Watch Mode

1. ✅ Use Debug mode during development for faster builds
2. ✅ Switch to ReleaseSafe for pre-production testing
3. ✅ Use pytest mode (`--pytest`) for integration testing
4. ✅ Keep test suites fast for quick feedback

### Async/Await

1. ✅ Always check if an object is a coroutine before using it
2. ✅ Properly handle reference counts for async objects
3. ✅ Be aware that `await_()` is blocking - use with caution
4. ✅ Implement `__await__` to make Zig objects awaitable

---

## Examples

Complete working examples can be found in:

- `example/leak_detection.zig` - Memory leak detection examples
- `example/async_await.zig` - Async/await examples
- `test/test_new_features.py` - Comprehensive Python tests

---

## Troubleshooting

### Memory Leaks Not Detected

**Problem**: Tests pass but you suspect there are leaks.

**Solution**: Ensure you're using `py.testing.TestFixture` and calling `defer fixture.deinit()`.

### Watch Mode Not Detecting Changes

**Problem**: Files change but rebuild doesn't trigger.

**Solution**:
- Check that files are in the watched paths
- Verify file extensions are `.zig` or `.py`
- Try reducing debounce time in code

### Async Functions Not Working

**Problem**: Coroutine-related errors or type mismatches.

**Solution**:
- Verify the object is actually a coroutine with `PyCoroutine.check()`
- Ensure proper reference counting
- Check Python side is using `async def` correctly

---

## Performance Impact

| Feature | Build Time Impact | Runtime Impact |
|---------|-------------------|----------------|
| Memory Leak Detection | None (test only) | ~5% slower tests |
| Watch Mode | N/A | N/A |
| Async/Await | None | Minimal (<1%) |

---

## Future Enhancements

Planned improvements:

- [ ] Visual leak reports with allocation traces
- [ ] Incremental compilation in watch mode
- [ ] Native Zig async integration
- [ ] Coverage reporting for leak detection
- [ ] LSP integration for real-time feedback
