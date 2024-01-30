import asyncio

class Ping:
    @staticmethod
    async def ping(host: str, count: int) -> str:
        try:
            proc = await asyncio.create_subprocess_shell(
                f'ping -c {count} {host}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
                )
            stdout, _ = await proc.communicate()
            # Decode the stdout and strip the trailing newline, then return only the avg time (ms)
            # return stdout.decode().strip().split('\n')[-1].split('=')[-1].split()[0].split('/')[1]
            return stdout.decode().strip()
        except Exception as e:
            # If an exception occurs, return an error message
            return f"Error: {str(e)}"

if __name__ == '__main__':
    # Test the ping method with a sample host
    async def main():
        result = await Ping.ping("1.1.1.1", 2)
        print(result)

    # Run the main function using asyncio
    asyncio.run(main())