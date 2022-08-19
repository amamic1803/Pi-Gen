from tkinter import *
import decimal
from math import factorial
from multiprocessing import Pool
import os
import sys
import pyperclip


def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

def pi_chudnovsky_algorithm_chunks(start, end, precision):
	decimal.getcontext().prec = precision

	base = start - 1
	M = decimal.Decimal(decimal.Decimal(factorial(6 * base)) / decimal.Decimal((factorial(3 * base) * (factorial(base) ** 3))))
	L = decimal.Decimal((545_140_134 * base) + 13_591_409)
	X = decimal.Decimal((- 262_537_412_640_768_000) ** base)
	K = decimal.Decimal((12 * base) - 6)

	sum_of_chunk = 0
	for i in range(start, end + 1):
		L += decimal.Decimal(545_140_134)
		K += decimal.Decimal(12)
		M *= decimal.Decimal(((K ** 3) - (16 * K)) / (i ** 3))
		X *= decimal.Decimal(- 262_537_412_640_768_000)

		sum_of_chunk += (M * L) / X

	return sum_of_chunk, (end - start + 1)

def pi_chudnovsky_algorithm(number_of_digits: int):
	decimal.getcontext().prec = int(number_of_digits * 1.0002) + 10

	if number_of_digits < 2000:
		C = decimal.Decimal(426_880) * (decimal.Decimal(10_005).sqrt())
		L = decimal.Decimal(13_591_409)
		X = decimal.Decimal(1)
		M = decimal.Decimal(1)
		K = decimal.Decimal(- 6)

		zbroj = (M * L) / X

		pi_old = C / zbroj
		i = decimal.Decimal(0)
		while True:
			i += decimal.Decimal(1)
			L += decimal.Decimal(545_140_134)
			K += decimal.Decimal(12)
			M *= decimal.Decimal(((K ** 3) - (16 * K)) / (i ** 3))
			X *= decimal.Decimal(- 262_537_412_640_768_000)

			zbroj += (M * L) / X

			pi_new = C / zbroj

			if pi_old == pi_new:
				break
			else:
				pi_old = pi_new

		pi_new = str(pi_new)[:number_of_digits + 2]
		return pi_new
	else:
		C = decimal.Decimal(426_880) * (decimal.Decimal(10_005).sqrt())

		L = decimal.Decimal(13_591_409)
		X = decimal.Decimal(1)
		M = decimal.Decimal(1)

		sum_of_series = (M * L) / X

		num_of_cpus = os.cpu_count()
		num_of_iterations = (number_of_digits // 14)
		if num_of_iterations % num_of_cpus != 0:
			num_of_iterations = ((num_of_iterations // num_of_cpus) + 1) * num_of_cpus
		chunk_size = 5 * num_of_cpus

		with Pool(processes=num_of_cpus) as pool:
			queue_list = []
			progress_queued = 0
			progress_completed = 0
			while True:
				if len(queue_list) < 2 * num_of_cpus and progress_queued != num_of_iterations:
					start_point = progress_queued + 1
					end_point = progress_queued + min(num_of_iterations - start_point + 1, chunk_size)
					queue_list.append(pool.apply_async(pi_chudnovsky_algorithm_chunks, args=(start_point, end_point, decimal.getcontext().prec)))
					progress_queued += end_point - start_point + 1
				elif progress_completed == num_of_iterations and len(queue_list) == 0:
					break
				else:
					out_chunk = queue_list[0].get()
					sum_of_series += out_chunk[0]
					progress_completed += out_chunk[1]
					queue_list.pop(0)

		return str(C / sum_of_series)[:number_of_digits + 2]

def validate_input(full_text):
	if " " in full_text or "-" in full_text:
		return False
	elif full_text == "":
		return True
	else:
		try:
			int(full_text)
			if len(full_text) <= 20:
				return True
			else:
				return False
		except ValueError:
			return False

def change_thickness_generate(event, thickness):
	digits_btn.config(highlightthickness=thickness)


if __name__ == '__main__':
	root = Tk()
	root.resizable(False, False)
	root.geometry(f"500x500+{(root.winfo_screenwidth() // 2) - 250}+{(root.winfo_screenheight() // 2) - 250}")
	root.title("Pi-Gen")
	root.iconbitmap(resource_path("pi-icon.ico"))
	root.config(background="#B2F3DE")

	reg = root.register(validate_input)

	pi_image = PhotoImage(file=resource_path("pi-image.png"))
	pi_image_label = Label(root, image=pi_image, background="#B2F3DE", activebackground="#B2F3DE", borderwidth=0, highlightthickness=0, anchor=CENTER)
	pi_image_label.place(x=60, y=30, width=100, height=100)

	title_label = Label(root, text="Pi-Gen", font=("Gabriola", 75, "italic", "bold"), foreground="#FFBC73", activeforeground="#FFBC73", background="#B2F3DE", activebackground="#B2F3DE", highlightthickness=0, borderwidth=0)
	title_label.place(x=185, y=30, width=250, height=100)

	digits_label = Label(root, text="Digits:", font=("Gabriola", 27, "bold"), foreground="#FFBC73", activeforeground="#FFBC73", background="#B2F3DE", activebackground="#B2F3DE", highlightthickness=0, borderwidth=0)
	digits_label.place(x=15, y=165, width=90, height=50)

	digits_ent = Entry(root, font=("Helvetica", 17), justify=CENTER, validate="key", validatecommand=(reg, "%P"), borderwidth=0, highlightthickness=3, highlightbackground="#ffffff", highlightcolor="#ffffff", disabledbackground="#354842", disabledforeground="#cccccc", background="#6a9185", foreground="#ffffff", insertbackground="#ffffff")
	digits_ent.place(x=110, y=170, width=280, height=40)
	digits_ent.insert(0, "25")

	digits_btn = Label(root, text="Generate", font=("Gabriola", 22, "bold"), foreground="#FFBC73", activeforeground="#FFBC73", background="#8ec2b1", activebackground="#8ec2b1", highlightthickness=2, highlightcolor="#ffffff", highlightbackground="#ffffff", borderwidth=0)
	digits_btn.place(x=395, y=170, width=100, height=40)
	digits_btn.bind("<Enter>", lambda event: change_thickness_generate(event, 4))
	digits_btn.bind("<Leave>", lambda event: change_thickness_generate(event, 2))

	root.mainloop()
