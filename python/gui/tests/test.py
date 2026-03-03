import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
a=Path(__file__).resolve()
print(a)
b=a.parents[1]
print(b)
c=b/"src"
print(c)
print(sys.path)
