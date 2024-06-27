class SuppressingContextManager:
    def __enter__(self):
        print("entering context")
        return self
    def __exit__(self,exc_type,exc_val, exc_tb):
        print("exiting context with exception")
        return true

with SuppressingContextManager():
        print("inside the block")
        raise ValueError("This is a test exception")
print("prog continues without visible exception")