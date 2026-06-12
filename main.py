import sys

class CompactSizeEncoder:
    def encode(self, value: int) -> bytes:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Input must be an integer")
        if value < 0:
            raise ValueError("Value cannot be negative")
        
        if value < 253:
            return bytes([value])
        elif value <= 0xFFFF:
            return b'\xfd' + value.to_bytes(2, byteorder='little')
        elif value <= 0xFFFFFFFF:
            return b'\xfe' + value.to_bytes(4, byteorder='little')
        elif value <= 0xFFFFFFFFFFFFFFFF:
            return b'\xff' + value.to_bytes(8, byteorder='little')
        else:
            raise ValueError("Value too large for 64-bit integer")


class CompactSizeDecoder:
    def decode(self, data: bytes) -> tuple[int, int]:
        if not data:
            raise ValueError("Data is too short")
        
        prefix = data[0]
        if prefix < 253:
            return prefix, 1
        elif prefix == 0xFD:
            if len(data) < 3:
                raise ValueError("Data too short")
            return int.from_bytes(data[1:3], byteorder='little'), 3
        elif prefix == 0xFE:
            if len(data) < 5:
                raise ValueError("Data too short")
            return int.from_bytes(data[1:5], byteorder='little'), 5
        elif prefix == 0xFF:
            if len(data) < 9:
                raise ValueError("Data too short")
            return int.from_bytes(data[1:9], byteorder='little'), 9


class TransactionData:
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.metadata = {}
        self.version = 1
        self.lock_time = 0

    def add_input(self, prev_txid: str, prev_vout: int, script_sig: str, sequence: int = 0xFFFFFFFF):
        self.inputs.append({
            "prev_txid": prev_txid,
            "prev_vout": prev_vout,
            "script_sig": script_sig,
            "sequence": sequence
        })

    def add_output(self, value: int, script_pubkey: str):
        self.outputs.append((value, script_pubkey))

    def get_input_details(self) -> list:
        print("--- Input Details")
        return self.inputs

    def summarize_outputs(self, min_value: int = 0) -> tuple[int, int]:
        print("--- Summarizing Outputs")
        total_satoshis = 0
        count = 0
        
        for i, (value, script_pubkey) in enumerate(self.outputs):
            if value < min_value or value < 0 or script_pubkey == "invalid":
                print(f"Skipping output {i}")
                continue
                
            total_satoshis += value
            count += 1
            print(f"Including output {i}")
            
            if total_satoshis > 1000000000:
                print("Total satoshis exceeded 1 Billion. Breaking summarization.")
                break
                
        return total_satoshis, count

    def update_metadata(self, new_meta: dict):
        self.metadata.update(new_meta)
        print("Updated metadata")

    def get_metadata_value(self, key: str, default=None):
        return self.metadata.get(key, default)

    def get_transaction_header(self) -> tuple[int, int, int, int]:
        return (self.version, len(self.inputs), len(self.outputs), self.lock_time)

    def set_transaction_header(self, version: int, num_inputs: int, num_outputs: int, lock_time: int):
        self.version = version
        self.lock_time = lock_time
        print("Set header via multiple assignment")


class UTXOSet:
    def __init__(self):
        self.utxos = set()

    def add_utxo(self, tx_id: str, vout: int, amount: int):
        self.utxos.add((tx_id, vout, amount))

    def remove_utxo(self, tx_id: str, vout: int, amount: int) -> bool:
        utxo = (tx_id, vout, amount)
        if utxo in self.utxos:
            self.utxos.remove(utxo)
            print("Removed UTXO")
            return True
        print("UTXO not found")
        return False

    def get_balance(self) -> int:
        return sum(utxo[2] for utxo in self.utxos)

    def find_sufficient_utxos(self, target_amount: int) -> set:
        accumulated = 0
        chosen_utxos = set()
        
        for utxo in self.utxos:
            chosen_utxos.add(utxo)
            accumulated += utxo[2]
            if accumulated >= target_amount:
                print("Found sufficient UTXOs")
                return chosen_utxos
                
        print("Could not find sufficient UTXOs")
        return set()

    def get_total_utxo_count(self) -> int:
        return len(self.utxos)

    def is_subset_of(self, other_set: 'UTXOSet') -> bool:
        return self.utxos.issubset(other_set.utxos)

    def combine_utxos(self, other_set: 'UTXOSet') -> 'UTXOSet':
        new_set = UTXOSet()
        new_set.utxos = self.utxos.union(other_set.utxos)
        return new_set

    def find_common_utxos(self, other_set: 'UTXOSet') -> 'UTXOSet':
        new_set = UTXOSet()
        new_set.utxos = self.utxos.intersection(other_set.utxos)
        return new_set


def generate_block_headers(prev_hash: str, merkle_root: str, timestamp: int, bits: int, start_nonce: int = 0, max_attempts: int = 1):
    print("--- Generating Block Headers")
    nonce = start_nonce
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        print(f"Attempt {attempts}:")
        
        yield {
            "version": 1,
            "prev_block_hash": prev_hash,
            "merkle_root": merkle_root,
            "timestamp": timestamp,
            "bits": bits,
            "nonce": nonce
        }
        
        if attempts % 100 == 0 and attempts < max_attempts:
            print(f"... {attempts} attempts made ...")
            
        nonce += 1