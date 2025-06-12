from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .utils import get_lined_text
import os


class TextedImage:
    def __init__(self):
        self.path = os.path.dirname(os.path.realpath(__file__)) + '/'
        self.template = Image.open(self.path + "template.png")
        self.canvas_mid = (self.template.width // 2, self.template.height // 2)

    def get(self, text: str):
        canvas_size = {'width': self.template.width, 'height': self.template.height}
        lines, font_size = get_lined_text(text, canvas_size)
        bytes_io = BytesIO()
        img = self.__add_lines_to_photo(lines, font_size)
        img.save(bytes_io, 'PNG')
        return bytes_io

    def __add_lines_to_photo(self, lines: str, font_size: int):
        img = self.template
        self.draw = ImageDraw.Draw(img)
        self.draw.font = ImageFont.truetype(
            font=self.path + "TT_Rationalist_Trial_Medium_Italic.ttf",
            size=font_size,
            encoding="unic"
        )
        self.draw.multiline_text(
            self.canvas_mid,
            lines,
            font=self.draw.font,
            align="center",
            anchor="mm",
        )

        return img


if __name__ == "__main__":
    texted_img = TextedImage()
    texted_img.get('Чмо пидор лох очконавт еблан сука шлюха тупая дебил дурак идиот имбицил инцел ебик долбоеб хуйло хуесос еблоид мразь тварь урод хуила чмырь даун пидор хуйлан пидрила шалава дурачье дурик уебан сволочь')
    