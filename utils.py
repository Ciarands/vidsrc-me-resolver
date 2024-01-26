import base64

class Utilities:
    @staticmethod
    def decode_src(encoded, seed) -> str:
        encoded_buffer = bytes.fromhex(encoded)
        decoded = ""
        for i in range(len(encoded_buffer)):
            decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
        return decoded

    @staticmethod
    def hunter(h, u, n, t, e, r) -> str:
        def hunter_def(d, e, f) -> int:
            charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
            source_base = charset[0:e]
            target_base = charset[0:f]

            reversed_input = list(d)[::-1]
            result = 0

            for power, digit in enumerate(reversed_input):
                if digit in source_base:
                    result += source_base.index(digit) * e**power

            converted_result = ""
            while result > 0:
                converted_result = target_base[result % f] + converted_result
                result = (result - (result % f)) // f

            return int(converted_result) or 0
        
        i = 0
        result_str = ""
        while i < len(h):
            j = 0
            s = ""
            while h[i] != n[e]:
                s += h[i]
                i += 1

            while j < len(n):
                s = s.replace(n[j], str(j))
                j += 1

            result_str += chr(hunter_def(s, e, 10) - t)
            i += 1

        return result_str

    @staticmethod
    def decode_base64_url_safe(s: str) -> bytearray:
        standardized_input = s.replace('_', '/').replace('-', '+')
        binary_data = base64.b64decode(standardized_input)
        return bytearray(binary_data)