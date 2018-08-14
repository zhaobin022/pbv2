from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import random
from django.shortcuts import reverse
from copy import deepcopy
from django.core.paginator import Paginator


class CustomPaginator(Paginator):
    def __init__(self,qs,request,page_size=5,show_pager_count=4):
        super(CustomPaginator, self).__init__(qs,page_size)
        self.request = request
        self.current_page_obj = self.get_current_page_obj()
        self.show_pager_count = show_pager_count

    def get_current_page_obj(self):
        current_page_num = self.request.GET.get('page',"")
        try:
            current_page_num = int(current_page_num)
        except Exception as e:
            current_page_num = 1

        return  self.page(current_page_num)

    def get_current_page_object_list(self):
        return self.current_page_obj.object_list


    def gen_page_html(self):

        html = ""

        front_tag = False
        back_tag = False
        half_show_count, remainder = divmod(self.show_pager_count, 2)


        if self.num_pages < self.show_pager_count:
            start = 1
            end = self.num_pages + 1
            if end -1 < self.num_pages:
                back_tag = True
        else:
            if self.current_page_obj.number <= half_show_count:
                start = 1
                end = self.show_pager_count + 1
                if end -1 < self.num_pages:
                    back_tag = True
            else:
                if self.current_page_obj.number + half_show_count > self.num_pages:
                    start = self.num_pages - self.show_pager_count + 1
                    end = self.num_pages + 1
                    if start != 1:
                        front_tag = True
                    if end-1 < self.num_pages:
                        back_tag = True

                else:

                    start = self.current_page_obj.number - half_show_count

                    end = self.current_page_obj.number + half_show_count
                    if remainder:
                        end += 1
                    if start != 1:
                        front_tag = True
                    if end-1 < self.num_pages:
                        back_tag = True

        if start >1:
            html += '''<button  class="btn btn-white" page="1">首页</button>'''



        if self.current_page_obj.has_previous():
            html += '''<button  class="btn btn-white" page="{}"><i class="fa fa-chevron-left"></i></button>'''.format(
                self.current_page_obj.previous_page_number())

        if front_tag:
            html+= '''<button  class="btn btn-white">..</button>'''

        for p in range(start,end):
            html+= '''<button page="{}" class="btn btn-white  {}">{}</button>'''.format(str(p),"active" if p == self.current_page_obj.number else "" ,str(p))

        if back_tag:
            html+= '''<button  class="btn btn-white">..</button>'''

        if self.current_page_obj.has_next():
            html+= '''<button page="{}" class="btn btn-white"><i class="fa fa-chevron-right"></i></button>'''.format(self.current_page_obj.next_page_number())

        if end-1 < self.num_pages:
            html += '''<button  class="btn btn-white" page="{}">尾页</button>'''.format(str(self.num_pages))

        return html
class ValidCodeImg:
    def __init__(self, width=150, height=30, code_count=4, font_size=32, point_count=20, line_count=3,
                 img_format='png'):
        '''
        可以生成一个经过降噪后的随机验证码的图片
        :param width: 图片宽度 单位px
        :param height: 图片高度 单位px
        :param code_count: 验证码个数
        :param font_size: 字体大小
        :param point_count: 噪点个数
        :param line_count: 划线个数
        :param img_format: 图片格式
        :return 生成的图片的bytes类型的data
        '''
        self.width = width
        self.height = height
        self.code_count = code_count
        self.font_size = font_size
        self.point_count = point_count
        self.line_count = line_count
        self.img_format = img_format

    @staticmethod
    def getRandomColor():
        '''获取一个随机颜色(r,g,b)格式的'''
        c1 = random.randint(0, 255)
        c2 = random.randint(0, 255)
        c3 = random.randint(0, 255)
        return (c1, c2, c3)

    @staticmethod
    def getRandomStr():
        '''获取一个随机字符串，每个字符的颜色也是随机的'''
        random_num = str(random.randint(0, 9))
        random_low_alpha = chr(random.randint(97, 122))
        random_upper_alpha = chr(random.randint(65, 90))
        random_char = random.choice([random_num, random_low_alpha, random_upper_alpha])
        return random_char

    def getValidCodeImg(self):
        # 获取一个Image对象，参数分别是RGB模式。宽150，高30，随机颜色
        image = Image.new('RGB', (self.width, self.height), self.getRandomColor())

        # 获取一个画笔对象，将图片对象传过去
        draw = ImageDraw.Draw(image)

        # 获取一个font字体对象参数是ttf的字体文件的目录，以及字体的大小
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_file_path = os.path.join(BASE_DIR,'pbv2','GOTHIC.TTF')
        font = ImageFont.truetype(font_file_path, size=self.font_size)

        temp = []
        for i in range(self.code_count):
            # 循环5次，获取5个随机字符串
            random_char = self.getRandomStr()

            # 在图片上一次写入得到的随机字符串,参数是：定位，字符串，颜色，字体
            draw.text((10 + i * 30, -2), random_char, self.getRandomColor(), font=font)

            # 保存随机字符，以供验证用户输入的验证码是否正确时使用
            temp.append(random_char)
        valid_str = "".join(temp)

        # 噪点噪线
        # 划线
        for i in range(self.line_count):
            x1 = random.randint(0, self.width)
            x2 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            y2 = random.randint(0, self.height)
            draw.line((x1, y1, x2, y2), fill=self.getRandomColor())

        # 画点
        for i in range(self.point_count):
            draw.point([random.randint(0, self.width), random.randint(0, self.height)], fill=self.getRandomColor())
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.arc((x, y, x + 4, y + 4), 0, 90, fill=self.getRandomColor())

        # 在内存生成图片
        from io import BytesIO
        f = BytesIO()
        image.save(f, self.img_format)
        data = f.getvalue()
        f.close()

        return data, valid_str


if __name__ == '__main__':
    # import os
    #
    #
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print(BASE_DIR)
    # img = ValidCodeImg()
    # data, valid_str = img.getValidCodeImg()
    # print(valid_str)
    #
    # f = open('test.png', 'wb')
    # f.write(data)