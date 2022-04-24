"""Main file for rendering relevant data"""


if __name__ == "__main__":
    # from ot3 import illustrate

    # BE CAREFUL!

    # There is a certain function, which changes the global
    # multiphonic fingerings DICT defined in constants/instruments.py
    # THEREFORE it is not safe (not even possible) to render the
    # sax notation via render.main() after illustrate.main().

    # illustrate.main()

    from ot3 import register
    from ot3 import render
    from ot3 import concatenate_score_parts

    # register.main()
    # render.main()
    concatenate_score_parts.main()
