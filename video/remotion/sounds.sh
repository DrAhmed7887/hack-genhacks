#!/bin/sh
# Sound effects and a soft music bed, synthesised with ffmpeg (no samples, no licences): video/public/sfx/.
#   sh video/sounds.sh <seconds>
set -e
D=$(dirname "$0")/public/sfx; mkdir -p "$D"; N=${1:-150}
f() { ffmpeg -loglevel error -y "$@"; }
f -f lavfi -i "anoisesrc=d=0.05:c=white:a=0.5" -af "highpass=f=2500,afade=t=out:st=0:d=0.05" -ar 48000 "$D/click.wav"
f -f lavfi -i "anoisesrc=d=0.8:c=pink:a=0.35" -af "bandpass=f=900:width_type=o:w=2,afade=t=in:d=0.4,afade=t=out:st=0.4:d=0.4" -ar 48000 "$D/whoosh.wav"
f -f lavfi -i "sine=f=1480:d=0.08" -af "afade=t=out:st=0:d=0.08,volume=0.35" -ar 48000 "$D/tick.wav"
f -f lavfi -i "aevalsrc='0.25*exp(-3*t)*(sin(2*PI*880*t)+0.6*sin(2*PI*1318.5*t))':d=1.4:s=48000" "$D/chime.wav"
# Pad: Am - F - C - G, 8 s each, every chord swelling in and out (changes fall on silence, so no clicks).
F1='if(lt(mod(t,32),8),220,if(lt(mod(t,32),16),174.61,if(lt(mod(t,32),24),261.63,196)))'
F2='if(lt(mod(t,32),8),261.63,if(lt(mod(t,32),16),220,if(lt(mod(t,32),24),329.63,246.94)))'
F3='if(lt(mod(t,32),8),329.63,if(lt(mod(t,32),16),261.63,if(lt(mod(t,32),24),392,293.66)))'
E='pow(sin(PI*mod(t,8)/8),0.6)'
f -f lavfi -i "aevalsrc='0.09*$E*(sin(2*PI*($F1)*t)+sin(2*PI*($F2)*t)+0.7*sin(2*PI*($F3)*t)+0.5*sin(PI*($F1)*t))':d=$N:s=48000" \
  -af "lowpass=f=1400,aecho=0.8:0.7:120|260:0.25|0.15,afade=t=in:d=2,afade=t=out:st=$((N-3)):d=3" "$D/music.wav"
echo "sfx → $D"
