# %% ####################### Initial connection
import pyvisa

rm = pyvisa.ResourceManager()

# %%
instrs = rm.list_resources()
print(instrs)
# %%
instr = rm.open_resource(instrs[0], read_termination='\n')
print(instr.query('*IDN?'))
# %%
instr.visa_timeout = 30000
print(instr.query('*IDN?'))

# %% ####################### Now do the setup

# %%

instr.write("INIT:CONT OFF")

# tracking generator
instr.write("OUTP:STAT ON")

# freq range
instr.write("SENS:FREQ:START 9.92MHZ")
instr.write("SENS:FREQ:STOP 10.05MHZ")

# sweep settings
instr.write("SENS:SWE:TIME:AUTO ON")
instr.write("SENS:SWE:POIN 3001")  # this does not work?

# markers
instr.write("CALC:MARK1:STAT ON")
instr.write("CALC:MARK1:CPEak:STATe ON")

instr.write("INIT:CONT ON")
# %%
# do one measurement for reference vals
instr.write("INIT:IMM; *WAI")

# %%
# now scale
instr.write("DISP:WIND:TRAC:Y:SCAL:AUTO ONCE")
# %%

# %% get marker
instr.query("CALC:MARK1:X?")
# %% get trace
instr.query_ascii_values("CALC:DATA? TRACE1")

# %%
instr.close()
# %%
# %%
instr.write('CALC:DATA? TRACE1')
data = instr.read_raw()
# %%
instr.query("CALC:MARK1:X?")
# %%
instr.write('CALC:MARK:FCOunt:STATe ON')
# %%
instr.write('CALC:MARK:FCOunt:STATe OFF')
# %%
instr.query('CALC:MARK:FCOunt:X?')

# %%
instr.query('CALC:MARK:FCOunt:STATe?')

# %%

from datetime import datetime, timedelta
# %%
now = datetime.now()
tenmin = [now + timedelta(minutes=t) for t in range(10)]
# %%
fiveago = tenmin[-1] - timedelta(minutes=4.9)
# %%
tenmin[fiveago:]

# %%
