from tkinter import *
from mpmath import mp, mpf
from math import factorial
from multiprocessing import Pool, freeze_support
from threading import Thread
import os
import sys
import pyperclip
import psutil
from tkinter.messagebox import showinfo, showerror


def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

def pi_chudnovsky_algorithm_chunks(start, end, precision):
	mp.dps = precision

	base = start - 1
	M = mpf(factorial(6 * base)) / mpf(factorial(3 * base) * (factorial(base) ** 3))
	L = mpf((545_140_134 * base) + 13_591_409)
	X = mpf((- 262_537_412_640_768_000) ** base)
	K = mpf((12 * base) - 6)

	sum_of_chunk = 0
	for i in range(start, end + 1):
		L += mpf(545_140_134)
		K += mpf(12)
		M *= mpf(((K ** 3) - (16 * K)) / (i ** 3))
		X *= mpf(- 262_537_412_640_768_000)

		sum_of_chunk += (M * L) / X

	return sum_of_chunk, (end - start + 1)

def pi_chudnovsky_algorithm(number_of_digits: int, gui_linked=False):
	global started, pi_generated, closed, pi_value

	try:
		mp.dps = int(number_of_digits * 1.0002) + 10 + 1

		if number_of_digits < 2000:
			C = mpf(426_880) * (mpf(10_005) ** 0.5)
			L = mpf(13_591_409)
			X = mpf(1)
			M = mpf(1)
			K = mpf(- 6)

			zbroj = (M * L) / X

			pi_old = C / zbroj
			i = mpf(0)
			while True:
				i += mpf(1)
				L += mpf(545_140_134)
				K += mpf(12)
				M *= mpf(((K ** 3) - (16 * K)) / (i ** 3))
				X *= mpf(- 262_537_412_640_768_000)

				zbroj += (M * L) / X

				pi_new = C / zbroj

				if pi_old == pi_new:
					break
				else:
					pi_old = pi_new

			pi_new = str(pi_new)[:number_of_digits + 2]
		else:
			C = mpf(426_880) * (mpf(10_005) ** 0.5)

			L = mpf(13_591_409)
			X = mpf(1)
			M = mpf(1)

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
					if closed:
						break
					elif len(queue_list) < 2 * num_of_cpus and progress_queued != num_of_iterations:
						start_point = progress_queued + 1
						end_point = progress_queued + min(num_of_iterations - start_point + 1, chunk_size)
						queue_list.append(pool.apply_async(pi_chudnovsky_algorithm_chunks, args=(start_point, end_point, mp.dps)))
						progress_queued += end_point - start_point + 1
					elif progress_completed == num_of_iterations and len(queue_list) == 0:
						break
					else:
						out_chunk = queue_list[0].get()
						sum_of_series += out_chunk[0]
						progress_completed += out_chunk[1]
						queue_list.pop(0)

						if gui_linked:
							output_label.config(text=f"Generating... {round((progress_completed / num_of_iterations) * 100, 1)} %")

			pi_new = str(C / sum_of_series)[:number_of_digits + 2]

		if closed:
			return
		elif gui_linked:
			started = False
			digits_ent.config(state="normal")
			digits_btn.config(background="#8ec2b1", activebackground="#8ec2b1", highlightthickness=2)
			if len(pi_new) > 42:
				output_label.config(text=f"{pi_new[:17]}...{pi_new[-25:]}")
			else:
				output_label.config(text=pi_new)
			pi_generated = True

		pi_value = pi_new

		return pi_new

	except (MemoryError, OverflowError, ValueError):
		if gui_linked:
			started = False
			digits_ent.config(state="normal")
			digits_btn.config(background="#8ec2b1", activebackground="#8ec2b1", highlightthickness=2)
			output_label.config(text="Ready")
			pi_generated = False
			showerror(title="Too big!", message="Can't calculate that many digits of Pi!", parent=root)
		else:
			raise Exception("Number of digits is too big!")

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
	global started
	if not started:
		digits_btn.config(highlightthickness=thickness)

def change_background_pi(event, color):
	global pi_generated
	if pi_generated:
		output_label.config(background=color, activebackground=color)

def generate_click(event):
	global started, pi_generated
	if not started:
		wanted_digits = digits_ent.get()
		if wanted_digits == "" or wanted_digits == "0":
			output_label.config(text="3")
			pi_generated = True
		else:

			started = True
			pi_generated = False
			digits_ent.config(state="disabled")
			digits_btn.config(background="#354842", activebackground="#354842", highlightthickness=2)
			output_label.config(text="Generating... 0.0 %", background="#B2F3DE")
			root.update_idletasks()

			generating_thread = Thread(target=pi_chudnovsky_algorithm, args=(int(wanted_digits), True))
			generating_thread.start()

def pi_click(event):
	global pi_generated, pi_value
	if pi_generated:
		pyperclip.copy(pi_value)
		showinfo(title="Copied!", message="Pi copied to clipboard!", parent=root)


if __name__ == '__main__':
	freeze_support()

	started = False
	pi_generated = False
	pi_value = ""
	closed = False

	root = Tk()
	root.resizable(False, False)
	root.geometry(f"500x290+{(root.winfo_screenwidth() // 2) - 250}+{(root.winfo_screenheight() // 2) - 145}")
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
	digits_btn.bind("<ButtonRelease-1>", generate_click)
	root.bind("<KeyPress-Return>", generate_click)

	output_label = Label(root, text="Ready", font=("Helvetica", 15, "bold"), anchor="center", justify="center", foreground="#FFBC73", activeforeground="#FFBC73", background="#B2F3DE", activebackground="#B2F3DE", highlightthickness=0, borderwidth=0)
	output_label.place(x=0, width=500, y=210, height=80)
	output_label.bind("<Enter>", lambda event: change_background_pi(event, "#c9f6e7"))
	output_label.bind("<Leave>", lambda event: change_background_pi(event, "#B2F3DE"))
	output_label.bind("<ButtonRelease-1>", pi_click)

	root.mainloop()
	closed = True
	psutil.Process(os.getpid()).kill()
