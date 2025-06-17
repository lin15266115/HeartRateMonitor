if  __name__ == '__main__':
    with open(r'_oldfiles\heart-rate.png', 'rb') as f:
        data = f.read()
        with open('UI/heartratepng.py', 'w') as g:
            g.write('img = "')
            g.write(data.hex())
            g.write('"')
            g.write("\n")
            g.write("heart_rate_png = bytes.fromhex(img)")
            g.write("\n")
            g.write("__all__ = ['heart_rate_png']")