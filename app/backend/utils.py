def visualize_graph(graph_instance, filename):
    print()
    print("Saving graph image to '" + filename + "'...")

    try:
        png_bytes = graph_instance.get_graph().draw_mermaid_png()

        with open(filename, "wb") as file_handle:
            file_handle.write(png_bytes)

        print("Done! Open " + filename + " to see the visualization.")
    except Exception as exc:
        print("Could not generate " + filename + ": " + str(exc))
