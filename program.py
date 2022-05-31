import zdo2022.main
import os.path


vdd = zdo2022.main.InstrumentTracker()


print("Napište název videa, které chcete zpracovat (video se musí nacházet v tomto adresáři):")
filename = input()
while not os.path.exists(filename):
    print("\nSoubor " + filename + " se bohužel v daném adresáři nenachází. Zkuste to prosím znovu:")
    filename = input()
print("\nBude zpracováno video", filename + ".")

prediction = vdd.predict(str(filename))