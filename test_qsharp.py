import qsharp

qsharp.init(target_profile=qsharp.TargetProfile.Base)

qsharp_code = """
operation Hello() : Unit {
    Message("Hello from Q#!");
}
"""

try:
    # In newer qsharp, you might need to use run or similar
    # qsharp.run("Hello()")
    qsharp.eval(qsharp_code)
    print("Eval successful")
except Exception as e:
    print(f"Eval failed: {e}")
