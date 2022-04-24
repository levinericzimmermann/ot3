from PyPDF2 import PdfFileMerger


def main():
    parts = (
        "ot3/constants/score/covers/cover.pdf",
        "ot3/constants/score/introductions/introduction.pdf",
        "builds/notations/oT3_violin.pdf",
        "builds/notations/oT3_saxophone.pdf",
    )

    merger = PdfFileMerger()
    for pdf in parts:
        merger.append(pdf)
    merger.write("builds/notations/ohneTitel3.pdf")
    merger.close()
