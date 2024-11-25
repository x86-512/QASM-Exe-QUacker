from math import pi, asin,sqrt
from qiskit import circuit
from qiskit import qasm3, transpile
from random import randint
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.circuit.library import MCMT, GroverOperator, MCXGate

from qiskit_aer import AerSimulator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager


from qiskit.visualization import plot_bloch_multivector

from sys import argv

def open_file(exe_name):
    with open(exe_name, 'rb') as exe:
        return exe.read()[0:2]

def calculate_iterations(n_qubits):
    return int((pi/4)/(asin(1/sqrt(1<<n_qubits)))-0.5)


    
def create_oracle(ciphertext):
    ciphertext_bytes = f"{ciphertext:08b}"[::-1]
    target = 77

    oracle = circuit.QuantumCircuit(9)

    oracle.x(8)
    oracle.h(8)

#Encode oracle as quantum circuit
    for i,ctrl in enumerate(ciphertext_bytes[:8]):
        if ctrl == '1':
            oracle.x(i)#Xor

    
    oracle.x(1)
    oracle.x(4)
    oracle.x(5)
    oracle.x(7)

    oracle.mcx([0,1,2,3,4,5,6,7], 8) #Causes phase kickback on the correct state (which will be in all 1's)

    oracle.x(7)
    oracle.x(5)
    oracle.x(4)
    oracle.x(1)
    
    for i,ctrl in enumerate(ciphertext_bytes[:8]):
        if ctrl == '1':
            oracle.x(i)#Xor

    oracle.h(8)
    oracle.x(8)
    return oracle

#Apply <-> gate to register in superposition and the target until you get 1*8
#If and only if
#Apply !^
def unencrypt_exe(key:int):
    crypted_str = b""
    with open(argv[1], 'rb') as exe:
        for i in exe.read()[:-1]: #Skip the added \n
            crypted_str+=(int(i)^key).to_bytes(1, 'little')
    with open(argv[1], 'wb') as exe:
        exe.write(crypted_str)
    print("Successfully decrypted "+argv[1])

def main():
    init_str = open_file(argv[1])
    if(isinstance(init_str, str)):
        ciphertext = ord(init_str[0])
    else:
        ciphertext = init_str[0]
    print("[+] Loaded encrypted malware sample")
    ciphertext_bytes = f"{ciphertext:08b}"
    target = 77
    target_bytes = f"{target:08b}"

    #Uniform superposition
    cracked_key = 0

    qreg = circuit.QuantumRegister(9, 'q')
    creg = circuit.ClassicalRegister(8, 'c')
    grover_circ = circuit.QuantumCircuit(qreg, creg)

    grover_circ.h(qreg[0])
    grover_circ.h(qreg[1])
    grover_circ.h(qreg[2])
    grover_circ.h(qreg[3])
    grover_circ.h(qreg[4])
    grover_circ.h(qreg[5])
    grover_circ.h(qreg[6])
    grover_circ.h(qreg[7])

    my_oracle = create_oracle(ciphertext)

    grover_operator = GroverOperator(my_oracle, insert_barriers=True)

    for _ in range(9): #17-20 ideal for simulation, 9 ideal for quantum hardware
        grover_circ.compose(grover_operator, inplace=True)
    
    grover_circ.measure(qreg[:8], creg)

    service = QiskitRuntimeService(channel="local")#Grovers breaks a lot more with SamplerV2, IDK why

    backend = service.least_busy()
    sampler = Sampler(mode=backend)
    runnable_circ = transpile(grover_circ, backend=backend)

    print("[-] Cracking encryption...")
    job = sampler.run([runnable_circ], shots=20) #Weak amplification, 7-8 is ideal # of shots
    result = job.result()
    print(f"Quantum Measurement Data: {result[0].data._data['c'].get_counts()}")

    runnable_circ.draw()
    result_prob_dist = result[0].data._data['c'].get_counts()
    key_bin = max(result_prob_dist, key=result_prob_dist.get)
    result_str = str(result)
    cracked_key = int(key_bin,2)

    print(f"[+] Cracked Key: {cracked_key}, Hex: {hex(cracked_key)}")

if __name__=="__main__":
    try:
        argv[1]
    except IndexError:
        print("File not specified")
        print(f"Try: python3 {__file__} <pe_file_here>")
        exit()
    main()
