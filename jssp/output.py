"""Export a schedule as a standalone SVG Gantt chart."""

from xml.etree.ElementTree import Element, SubElement, ElementTree


def write_gantt(schedule, n_machines, path):
    """Draw machine rows with operation labels using only the standard library."""
    makespan = max((op["finish"] for op in schedule), default=1)
    scale = 1000 / max(makespan, 1)
    root = Element("svg", xmlns="http://www.w3.org/2000/svg",
                   width="1160", height=str(100 + 60 * n_machines))
    SubElement(root, "rect", width="100%", height="100%", fill="white")

    def label(x, y, text, size=14):
        SubElement(root, "text", x=str(x), y=str(y),
                   attrib={"font-family": "sans-serif", "font-size": str(size)}).text = text

    label(80, 25, f"Job shop schedule | Makespan: {makespan}", 20)
    for machine in range(n_machines):
        label(15, 76 + machine * 60, f"M{machine}")
        SubElement(root, "line", x1="80", x2="1080", y1=str(90 + machine * 60),
                   y2=str(90 + machine * 60), stroke="#dddddd")
    for op in schedule:
        x, y = 80 + op["start"] * scale, 50 + op["machine"] * 60
        width = (op["finish"] - op["start"]) * scale
        rect = SubElement(root, "rect", x=str(x), y=str(y), width=str(width),
                          height="38", fill=f"hsl({op['job'] * 137.5 % 360},60%,75%)",
                          stroke="white")
        text = f"J{op['job']} O{op['operation']}: {op['start']}-{op['finish']}"
        SubElement(rect, "title").text = text
        if width > 32:
            label(x + 3, y + 24, f"J{op['job']}", 11)
    for tick in range(11):
        label(80 + tick * 100, 70 + n_machines * 60, str(round(makespan * tick / 10)))
    ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
