import asyncio
from app.infrastructure.docker.cpp_sandbox import execute_cpp_secure
import pprint

async def main():
    print("Testing valid C++ code...")
    valid_code = """
    #include <iostream>
    using namespace std;
    int main() {
        cout << "Hello Sandbox!" << endl;
        return 0;
    }
    """
    res = await execute_cpp_secure(valid_code)
    pprint.pprint(res)
    
    print("\nTesting infinite loop (TLE)...")
    tle_code = """
    #include <iostream>
    int main() {
        while(true) {}
        return 0;
    }
    """
    res = await execute_cpp_secure(tle_code, timeout_seconds=2)
    pprint.pprint(res)

    print("\nTesting Fork Bomb...")
    fork_bomb = """
    #include <unistd.h>
    int main() {
        while(1) { fork(); }
        return 0;
    }
    """
    res = await execute_cpp_secure(fork_bomb)
    pprint.pprint(res)

if __name__ == "__main__":
    asyncio.run(main())
