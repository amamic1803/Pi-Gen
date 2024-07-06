import collections
import ctypes
import os
import sys
import tkinter as tk
from math import factorial
from multiprocessing import Pool, freeze_support, Value
from threading import Thread
from tkinter.messagebox import showinfo, showerror

import psutil
import pyperclip
from mpmath import mp, mpf  # take care that gmpy2 is also installed, improves speed of mpmath drastically


class App:
	def __init__(self):
		self.working: bool = False
		self.working_thread = None
		self.pi_value: str = ""
		self.killswitch = Value(ctypes.c_bool, True)

		self.root = tk.Tk()
		self.root.geometry(f"500x290"
		                   f"+{(self.root.winfo_screenwidth() // 2) - 250}"
		                   f"+{(self.root.winfo_screenheight() // 2) - 145}")
		self.root.resizable(False, False)
		self.root.title("Pi-Gen")
		self.root.iconbitmap(self.resource_path("resources/pi-icon.ico"))
		self.root.config(background="#B2F3DE")

		self.pi_img = tk.PhotoImage(file=self.resource_path("resources/pi-image.png"))
		self.pi_img_lbl = tk.Label(self.root, image=self.pi_img, background="#B2F3DE", activebackground="#B2F3DE",
		                           borderwidth=0, highlightthickness=0, anchor=tk.CENTER)
		self.pi_img_lbl.place(x=60, y=30, width=100, height=100)

		self.title_lbl = tk.Label(self.root, text="Pi-Gen", font=("Gabriola", 75, "italic", "bold"),
		                          foreground="#FFBC73", activeforeground="#FFBC73",
		                          background="#B2F3DE", activebackground="#B2F3DE",
		                          highlightthickness=0, borderwidth=0)
		self.title_lbl.place(x=185, y=30, width=250, height=100)

		self.digits_lbl = tk.Label(self.root, text="Digits:", font=("Gabriola", 27, "bold"),
		                           foreground="#FFBC73", activeforeground="#FFBC73",
		                           background="#B2F3DE", activebackground="#B2F3DE",
		                           highlightthickness=0, borderwidth=0)
		self.digits_lbl.place(x=15, y=165, width=90, height=50)

		self.reg = self.root.register(self.validate_int)
		self.digits_ent = tk.Entry(self.root, font=("Helvetica", 17), justify=tk.CENTER,
		                           validate="key", validatecommand=(self.reg, "%P"),
		                           borderwidth=0, highlightthickness=3, highlightbackground="#ffffff", highlightcolor="#ffffff",
		                           disabledbackground="#354842", disabledforeground="#cccccc",
		                           background="#6a9185", foreground="#ffffff", insertbackground="#ffffff")
		self.digits_ent.place(x=110, y=170, width=280, height=40)
		self.digits_ent.insert(0, "25")

		self.generate_btn = tk.Label(self.root, text="Generate", font=("Gabriola", 22, "bold"), cursor="hand2",
		                             foreground="#FFBC73", activeforeground="#FFBC73",
		                             background="#8ec2b1", activebackground="#8ec2b1",
		                             highlightthickness=2, highlightcolor="#ffffff", highlightbackground="#ffffff", borderwidth=0)
		self.generate_btn.place(x=395, y=170, width=100, height=40)
		self.generate_btn.bind("<Enter>", lambda event: self.generate_btn.config(highlightthickness=4) if not self.working else None)
		self.generate_btn.bind("<Leave>", lambda event: self.generate_btn.config(highlightthickness=2) if not self.working else None)
		self.generate_btn.bind("<ButtonRelease-1>", lambda event: self.generate_click())
		self.root.bind("<KeyPress-Return>", lambda event: self.generate_click())

		self.output_lbl = tk.Label(self.root, text="Ready", font=("Helvetica", 15, "bold"),
		                           anchor="center", justify="center",
		                           foreground="#FFBC73", activeforeground="#FFBC73",
		                           background="#B2F3DE", activebackground="#B2F3DE",
		                           highlightthickness=0, borderwidth=0)
		self.output_lbl.place(x=0, width=500, y=210, height=80)
		self.output_lbl.bind("<Enter>", lambda event: self.output_lbl.config(background="#C9F6E7", activebackground="#C9F6E7") if self.pi_value != "" else None)
		self.output_lbl.bind("<Leave>", lambda event: self.output_lbl.config(background="#B2F3DE", activebackground="#B2F3DE") if self.pi_value != "" else None)
		self.output_lbl.bind("<ButtonRelease-1>", lambda event: self.pi_click())

		self.root.mainloop()

		self.killswitch.value = False
		try:
			self.working_thread.join()
		except AttributeError:
			pass
		psutil.Process(os.getpid()).kill()

	def pi_click(self):
		if self.pi_value != "":
			pyperclip.copy(self.pi_value)
			showinfo(title="Copied!", message="Pi copied to clipboard!", parent=self.root)

	def generate_click(self):
		if self.working:
			return

		wanted_digits = self.digits_ent.get()
		if wanted_digits == "" or wanted_digits == "0":
			self.pi_value = ""
			self.output_lbl.config(text="Ready", cursor="arrow")
		else:
			self.working = True
			self.pi_value = ""
			self.digits_ent.config(state="disabled")
			self.generate_btn.config(background="#354842", activebackground="#354842", highlightthickness=2, cursor="arrow")
			self.output_lbl.config(cursor="arrow")
			self.update_progress(0.0)
			self.root.update_idletasks()
			self.working_thread = Thread(target=self.worker, args=(int(wanted_digits), ))
			self.working_thread.start()

	def update_progress(self, progress: float):
		progress_percent = progress * 100
		int_part = int(progress_percent)
		dec_part = int((progress_percent - int_part) * 100)
		self.output_lbl.config(text=f"Generating... {int_part:3}.{dec_part:02} %")

	def worker(self, digits: int):
		chudnovsky = Chudnovsky(digits)
		self.update_progress(chudnovsky.progress)

		def wrapper(result_status: Value):
			result_status.value = chudnovsky.generate_pi(self.killswitch)

		result_status = Value(ctypes.c_bool, False)
		chudnovsky_thread = Thread(target=wrapper, args=[result_status], daemon=True)
		chudnovsky_thread.start()

		while chudnovsky_thread.is_alive():
			self.update_progress(chudnovsky.progress)
			self.root.update_idletasks()
			chudnovsky_thread.join(0.1)

		try:
			self.working = False
			self.digits_ent.config(state="normal")
			self.generate_btn.config(background="#8ec2b1", activebackground="#8ec2b1", highlightthickness=2, cursor="hand2")
			if result_status.value:
				self.pi_value = chudnovsky.get_pi()

				if len(self.pi_value) > 42:
					self.output_lbl.config(text=f"{self.pi_value[:17]}...{self.pi_value[-25:]}")
				else:
					self.output_lbl.config(text=self.pi_value)
				self.output_lbl.config(cursor="hand2")
			else:
				self.output_lbl.config(text="Ready", cursor="arrow")
				self.pi_value = ""
				showerror(title="Too big!", message="Can't calculate that many digits of Pi!", parent=self.root)
		except AttributeError:  # GUI closed
			pass

	@staticmethod
	def resource_path(relative_path):
		""" Get absolute path to resource, works for dev and for PyInstaller """
		try:
			# PyInstaller creates a temp folder and stores path in _MEIPASS
			base_path = sys._MEIPASS
		except AttributeError:
			base_path = os.path.abspath(".")
		return os.path.join(base_path, relative_path)

	@staticmethod
	def validate_int(full_text) -> bool:
		""" Validate if the input is a positive integer, or empty string. """

		if " " in full_text or "-" in full_text:
			return False
		elif full_text == "":
			return True
		else:
			try:
				int(full_text)
				return len(full_text) <= 20
			except ValueError:
				return False


class Chudnovsky:
	def __init__(self, digits: int):
		self.digits = digits
		self.precision = int(self.digits * 1.0002) + 10 + 1
		self.pi = None
		self.progress = 0.0  # 0.0 - 1.0

	def get_pi(self) -> str:
		if self.pi is None:
			raise Exception("Pi not generated yet!")
		return str(self.pi)[:self.digits + 2]

	def generate_pi(self, killswitch: Value) -> bool:
		try:
			self.progress = 0.0
			mp.dps = self.precision

			C = mpf(426_880) * (mpf(10_005) ** 0.5)
			L = mpf(13_591_409)
			X = mpf(1)
			M = mpf(1)
			sum_of_series = (M * L) / X

			num_of_iterations = self.precision // 14

			if self.precision < 2000:
				out_chunk = self.process_chunk(1, num_of_iterations, self.precision)
				sum_of_series += out_chunk[0]
				self.progress = 100.0
			else:
				num_of_cpus = os.cpu_count()
				if num_of_iterations % num_of_cpus != 0:
					num_of_iterations = ((num_of_iterations // num_of_cpus) + 1) * num_of_cpus
				chunk_size = 5 * num_of_cpus

				with Pool(processes=num_of_cpus) as pool:
					queue_list = collections.deque()
					progress_queued = 0
					progress_completed = 0
					while killswitch.value:
						if len(queue_list) < 2 * num_of_cpus and progress_queued != num_of_iterations:
							start_point = progress_queued + 1
							end_point = progress_queued + min(num_of_iterations - start_point + 1, chunk_size)
							queue_list.append(
								pool.apply_async(self.process_chunk, args=(start_point, end_point, self.precision)))
							progress_queued += end_point - start_point + 1
						elif progress_completed == num_of_iterations and len(queue_list) == 0:
							break
						else:
							out_chunk = queue_list[0].get()
							sum_of_series += out_chunk[0]
							progress_completed += out_chunk[1]
							queue_list.popleft()
							self.progress = progress_completed / num_of_iterations

			self.pi = C / sum_of_series

			return True
		except (MemoryError, OverflowError, ValueError):
			return False

	@staticmethod
	def process_chunk(start, end, precision):
		mp.dps = precision

		base = start - 1
		M = mpf(factorial(6 * base)) / mpf(factorial(3 * base) * (factorial(base) ** 3))
		L = mpf((545_140_134 * base) + 13_591_409)
		X = mpf((- 262_537_412_640_768_000) ** base)
		K = mpf((12 * base) - 6)

		L_ADD = mpf(545_140_134)
		K_ADD = mpf(12)
		X_MUL = mpf(- 262_537_412_640_768_000)

		sum_of_chunk = 0
		for i in range(start, end + 1):
			L += L_ADD
			K += K_ADD
			M *= mpf(((K ** 3) - (16 * K)) / (i ** 3))
			X *= X_MUL

			sum_of_chunk += (M * L) / X

		return sum_of_chunk, (end - start + 1)


if __name__ == '__main__':
	freeze_support()
	App()
