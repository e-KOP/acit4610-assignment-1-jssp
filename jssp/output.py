"""Export a schedule as a standalone SVG Gantt chart."""

from colorsys import hls_to_rgb
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
        # Hex colors also render correctly in SVG-to-PDF/image converters.
        rgb = hls_to_rgb((op["job"] * 137.5 % 360) / 360, 0.75, 0.6)
        color = "#" + "".join(f"{round(channel * 255):02x}" for channel in rgb)
        rect = SubElement(root, "rect", x=str(x), y=str(y), width=str(width),
                          height="38", fill=color,
                          stroke="white")
        text = f"J{op['job']} O{op['operation']}: {op['start']}-{op['finish']}"
        SubElement(rect, "title").text = text
        if width > 32:
            label(x + 3, y + 24, f"J{op['job']}", 11)
    ticks = min(10, max(1, int(makespan)))
    for tick in range(ticks + 1):
        label(80 + tick * 1000 / ticks, 70 + n_machines * 60,
              str(round(makespan * tick / ticks)))
    ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_json(path, value):
    """Write a readable JSON artifact."""
    import json
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    """Write nonempty rows with a shared field order."""
    import csv
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plotting():
    """Use a headless backend so plotting also works on servers and in CI."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def save_result(result, output, make_plot=True):
    """Export one validated GA result and its decoded schedule."""
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "solution.json", result)
    write_csv(output / "schedule.csv", result["schedule"])
    write_csv(output / "history.csv", result["history"])
    n_machines = max(item["machine"] for item in result["schedule"]) + 1
    write_gantt(result["schedule"], n_machines, output / "gantt.svg")
    if make_plot:
        plt = plotting()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        history = result["history"]
        ax.plot([h["generation"] for h in history],
                [h["generation_best"] for h in history], label="Current generation")
        ax.plot([h["generation"] for h in history],
                [h["best_so_far"] for h in history], label="Best observed")
        ax.set(xlabel="Generation", ylabel="Makespan",
               title=f"{result['instance']} | seed {result['seed']}")
        ax.legend()
        ax.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(output / "convergence.png", dpi=160)
        plt.close(fig)


def plot_experiments(curves, summaries, output):
    """Compare mean convergence and mean optimality gap for all six instances."""
    plt = plotting()
    instances = list(dict.fromkeys(row["instance"] for row in summaries))
    names = list(dict.fromkeys(row["parameter_set"] for row in summaries))
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    # Fill columns: small (la01/la02), medium (la16/la17), large (la31/la32).
    for ax, instance in zip(axes.T.flat, instances):
        for name in names:
            points = [r for r in curves if r["instance"] == instance
                      and r["parameter_set"] == name]
            ax.plot([r["generation"] for r in points],
                    [r["mean_best_so_far"] for r in points], label=name)
        ax.set(title=instance, xlabel="Generation", ylabel="Mean best observed makespan")
        ax.grid(alpha=0.2)
    axes.flat[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "convergence.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, instance in zip(axes.flat, instances):
        rows = [r for r in summaries if r["instance"] == instance]
        ax.bar(range(len(rows)), [r["mean_gap_percent"] for r in rows],
               yerr=[r["std_gap_percent"] for r in rows], capsize=4,
               color=["#2874a6", "#148f77", "#b9770e"])
        ax.set_xticks(range(len(rows)), [r["parameter_set"].replace("_", "\n") for r in rows])
        ax.set(title=instance, ylabel="Gap to reference optimum (%)")
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Mean gap across independent runs; error bars show sample standard deviation")
    fig.tight_layout()
    fig.savefig(output / "quality_comparison.png", dpi=160)
    plt.close(fig)
