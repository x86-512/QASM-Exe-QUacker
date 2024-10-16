from math import pi, asin,sqrt
from qiskit import circuit
from qiskit import qasm3
from random import randint
from qiskit.primitives import Sampler
#from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.circuit.library import MCMT, GroverOperator, MCXGate

from qiskit_aer import AerSimulator
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qiskit.visualization import plot_bloch_multivector


from sys import argv

def open_file(exe_name):
    with open(exe_name) as exe:
        return exe.read()[0:2]

def calculate_iterations(n_qubits):
    return int((pi/4)/(asin(1/sqrt(1<<n_qubits)))-0.5)


    
def create_oracle(ciphertext):
    ciphertext_bytes = f"{ciphertext:08b}"[::-1]
    target = 77
    #target_bytes = f"{target:08b}"[::-1]

    #x = 45
    #x_bytes = f"{x:08b}"[::-1]

    oracle = circuit.QuantumCircuit(9)

    oracle.x(8)
    oracle.h(8)

    #for i, ctrl in enumerate(x_bytes, start=1): #This just sets up the key
    #    if ctrl=='1':
    #        oracle.x(i) #Key
#Encode oracle as quantum circuit
    for i,ctrl in enumerate(ciphertext_bytes[:8]):
        if ctrl == '1':
            oracle.x(i)#Xor

    #oracle.x(0)
    #oracle.x(2)
    #oracle.x(3)
    #oracle.x(6)
    
    oracle.x(1)
    oracle.x(4)
    oracle.x(5)
    oracle.x(7)

    #for i in range(8):
    #    oracle.x(i)

    #mcx = MCXGate(8) #Need to cause phase kickback
    #oracle.append(mcx, [1,2,3,4,5,6,7,8,0])
    oracle.mcx([0,1,2,3,4,5,6,7], 8)

    oracle.x(7)
    oracle.x(5)
    oracle.x(4)
    oracle.x(1)

    #for i in range(8):
    #    oracle.x(i)
     
    #oracle.x(6)
    #oracle.x(3)
    #oracle.x(2)
    #oracle.x(0)
    
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
            #print(int(i))
            #print((int(i)^key))
            #print(bytes(int(i)^key))
            crypted_str+=(int(i)^key).to_bytes(1, 'little')
    #print(crypted_str)
    with open(argv[1], 'wb') as exe:
        exe.write(crypted_str)
    print("Successfully decrypted "+argv[1])

def main():
    ciphertext = ord(open_file(argv[1])[0])
    #n_iterations = calculate_iterations(8)
    #print(ciphertext)
    #print(ciphertext^77)
    #ciphertext = 96
    ciphertext_bytes = f"{ciphertext:08b}"
    target = 77
    target_bytes = f"{target:08b}"

    #Uniform superposition
    cracked_key = 0
    while True:

        qreg = circuit.QuantumRegister(9, 'q')
        creg = circuit.ClassicalRegister(8, 'c')
        grover_circ = circuit.QuantumCircuit(qreg, creg)

        grover_circ.h(qreg[i] for i in range(8))

        my_oracle = create_oracle(ciphertext)

        grover_operator = GroverOperator(my_oracle, insert_barriers=True)

        for i in range(17): #17
            #grover_circ.compose(my_oracle, inplace=True)
            grover_circ.compose(grover_operator, inplace=True)
            #grover_circ.append(grover_operator, range(9))
            
            #grover_circ.h(qreg[i] for i in range(8))
            #grover_circ.x(qreg[i] for i in range(8))
            #grover_circ.h(7)
            #grover_circ.cz(qreg[:7],7)
            #grover_circ.h(7)
            #grover_circ.x(qreg[i] for i in range(8))
            #grover_circ.h(qreg[i] for i in range(8))
        
        grover_circ.measure(qreg[:8], creg)


        sampler = Sampler()
        job = sampler.run(grover_circ, shots=1) #Weak amplification
        #print(job.result())
        #print(type(job.result()))
        result_str = str(job.result())
        cracked_key = int(result_str[result_str.find('{')+1:result_str.find(':')]) #I will not run multiple shots
        if ciphertext^cracked_key == target:
            break

    print(f"Cracked Key: {cracked_key}, Hex: {hex(cracked_key)}")
    unencrypt_exe(cracked_key)
    
    #backend = AerSimulator(method='statevector')
        
    #backend.set_options(
    #    max_parallel_threads = 0,
    #    max_parallel_experiments = 0,
    #    max_parallel_shots = 1,
    #    statevector_parallel_threshold = 16     
    #)
        
    #pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    #qc_combine = pm.run(grover_circ)

    #result = backend.run(qc_combine, shots= 1)
    
    #psi_out_complex = result.result()
    #plot_bloch_multivector(psi_out_complex.get_statevector())
    #print(psi_out_complex)
    
    #test_oracle()

    
    #sample = qiskit_ibm_runtime.Sampler(mode=backend)
    #job = execute(oracle, backend, shots=1)

if __name__=="__main__":
    main()
