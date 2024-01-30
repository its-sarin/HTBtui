import subprocess

def ping_host(host):
    try:
        # Use subprocess to execute the ping command and capture the output
        output = subprocess.check_output(["ping", "-c", "4", host], stderr=subprocess.STDOUT, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        # If the ping command fails, return an error message
        return f"Error: {e.output}"

if __name__ == '__main__':
    # Test the function with a sample host
    result = ping_host("1.1.1.1")
    print(result)