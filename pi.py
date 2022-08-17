import decimal
import time

def pi_chudnovsky_algorithm(number_of_digits: int):
	decimal.getcontext().prec = number_of_digits * 2

	C = decimal.Decimal(426_880) * (decimal.Decimal(10_005).sqrt())
	L = decimal.Decimal(13_591_409)
	X = decimal.Decimal(1)
	M = decimal.Decimal(1)
	K = decimal.Decimal(- 6)

	zbroj = (M * L) / X

	pi_old = C * (zbroj ** -1) * (10 ** number_of_digits)

	i = decimal.Decimal(0)
	while True:
		i += decimal.Decimal(1)
		L += decimal.Decimal(545_140_134)
		K += decimal.Decimal(12)
		M *= decimal.Decimal(((K ** 3) - (16 * K)) / (i ** 3))
		X *= decimal.Decimal(- 262_537_412_640_768_000)

		zbroj += (M * L) / X

		pi_new = C * (zbroj ** -1) * (10 ** number_of_digits)

		if str(pi_old) == str(pi_new):
			break
		else:
			pi_old = pi_new

	pi_new = str(pi_new).split(".")[0][1:]
	pi_new = f"3.{pi_new}"

	return pi_new


if __name__ == '__main__':
	digits = int(input("Number of PI digits: "))
	start = time.time()
	pie = pi_chudnovsky_algorithm(digits)
	print(pie)
	print(len(pie))
	print(time.time() - start)
