import requests
from subprocess import call
import os
from bs4 import BeautifulSoup
import unicodedata
import string

validFilenameChars = "-_.() ?%s%s" % (string.ascii_letters, string.digits)


def removeDisallowedFilenameChars(filename):
    cleanedFilename = unicodedata.normalize('NFKD', filename)
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)


class PlatziDl:
    LOGIN_URL = "https://courses.platzi.com/login/"
    EMAIL = ""
    PASSWORD = "321access"

    def __init__(self, course_url):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"})
        self.login()
        self.process_course(course_url)

    def login(self):
        r = self.session.get(self.LOGIN_URL)
        token = BeautifulSoup(r.text, "lxml").find("input", {"name": "csrfmiddlewaretoken"})['value']
        self.session.headers.update({"Referer": self.LOGIN_URL})
        self.session.post(self.LOGIN_URL,
                          data={"csrfmiddlewaretoken": token, "email": self.EMAIL, "password": self.PASSWORD})
        self.session.headers.pop("Referer")

    def process_course(self, url: str):
        r = self.session.get(url)
        bs = BeautifulSoup(r.text, "lxml")
        elems = bs.find_all("a", {"class": "Material-link"})
        links = [("https://platzi.com" + e['href'], e['title'].strip()) for e in elems]
        for link, title in links:
            self.get_video_link(link, title)

    def get_video_link(self, url: str, title: str):
        r = self.session.get(url)
        bs = BeautifulSoup(r.text, "lxml")
        scripts = bs.find_all("script")
        # title = bs.find("title").text.strip()
        for s in scripts:
            # if "youtube.com/embed" in s.text:
            #     t = s.text[s.text.index("youtube.com/embed"):]
            #     t = t[:t.index('"')]
            #     print(t)
            #     # TODO... yt-dl here
            if "https://mdstrm.com/video/" in s.text:
                t = s.text[s.text.index("https://mdstrm.com/video/"):]
                t = t[:t.index('"')]
                self.mdstrm_dl(t, title)
                break

    def mdstrm_dl(self, url: str, title: str):
        print("Attempting {} download".format(title))
        r = self.session.get(url)
        r = self.session.get(r.text.split("\n")[-1])
        lines = r.text.split("\n")
        subfiles = []
        lines_count = sum(not line.startswith('#') for line in lines) - 1
        i = 1
        with open(".list.txt", "w"):
            pass
        with open(".list.txt", "a") as listF:
            for line in lines:
                if line.startswith('#') or not line: continue
                name = line[line.index(".mp4/") + 5:line.index("?access")]
                subfiles.append(name)
                r = self.session.get(line)
                with open(name, "wb") as F:
                    F.write(r.content)
                listF.write("file '{}'\n".format(name))
                print("Downloaded partial video file {}/{}".format(i, lines_count))
                i += 1
        FNULL = open(os.devnull, 'w')
        call("ffmpeg -f concat -safe 0 -i .list.txt -c copy {}.mp4".format(
            removeDisallowedFilenameChars(title).replace(' ', '_')).split(), stdout=FNULL)
        FNULL.close()
        print("Joined files into {}.mp4".format(title))
        print("Deleting partial files...")
        for name in subfiles:
            os.remove(name)
        os.remove(".list.txt")
        print("Done.")


if __name__ == "__main__":
    d = PlatziDl("https://platzi.com/clases/programacion-basica/")
    # d.login()
    # d.get_video("https://platzi.com/clases/programacion-basica/concepto/bienvenido-al-curso0560/bienvenidos/material/")
    # d.get_video_link(
    #    "https://platzi.com/clases/programacion-basica/concepto/programacion-de-hardware-y-electronica-con-arduino/construye-un-robot-con-javascript/material/")
