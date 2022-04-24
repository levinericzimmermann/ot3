sr     = 48000
ksmps  = 1
0dbfs  = 1
nchnls = 1


instr 1
    icps = p4
    icontrolamp = p5
    iattack = p3 * 0.2
    irelease = p3 * 0.15
    isustain = p3 - iattack - irelease
    iminmod = p6
    iglissfactor = p7
    iglissduration = p8 * p3

    kenvelopefreq linseg iglissfactor, iglissduration, 1

    kenvelopeamp linseg 0, iattack, 1 , isustain, 1, irelease, 0
    kampmodulatormodulator randomi 3, 7, 0.2, 3
    kampmodulator randomi iminmod, 1.15, kampmodulatormodulator, 3

    asig poscil kenvelopeamp * icontrolamp * kampmodulator, icps * kenvelopefreq

    out asig
endin
