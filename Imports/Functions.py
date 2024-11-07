import csv  	# for plot_f1_score
import locale  	# For wifi_is_connected
import os  		# for model_exist
import platform
import subprocess
import sys

try :
	import matplotlib.pyplot as plt  	# for plot_confusion_matrix and plot_precision_recall_curve
	import seaborn as sns  				# for plot_confusion_matrix
	from sklearn.metrics import precision_recall_curve  # for plot_precision_recall_curve
	from sklearn.metrics import precision_recall_fscore_support, accuracy_score, classification_report  # for plot_f1_score
except ModuleNotFoundError as Err :
	missing_module = str(Err).replace('No module named ','')
	missing_module = missing_module.replace("'",'')
	if missing_module == 'cv2' :
		sys.exit(f'No module named {missing_module} try : pip install opencv-python')
	if missing_module == 'sklearn' :
		sys.exit(f'No module named {missing_module} try : pip install scikit-learn')
	else :
		print(f'No module named {missing_module} try : pip install {missing_module}')

def connected_wifi() :
	os_name = platform.system()
	region = locale.getlocale()

	if os_name == "Windows" :
		if region[0][:-3] == 'fr' :
			list_current_networks_command = "netsh wlan show interfaces"
			network_output = subprocess.check_output(list_current_networks_command, encoding="437")
			str_n_out = str(network_output)
			start_idx = str_n_out.find('État') + 24

			if not str_n_out[start_idx] == 'c':
				sys.exit('Not connected to Wifi')

			Wifi_SSID = ''
			for i in range(start_idx+38, len(str_n_out)) :
				if str_n_out[i] == "\n" :
					break
				Wifi_SSID += str_n_out[i]

			return True, Wifi_SSID
		
		else : 
			print(f'Windows {region[0][:-3].upper()} is not supported')
			return False, 0

	elif os_name == "Linux" :
		try : 
			list_current_networks_command = 'nmcli d'
			network_output = subprocess.check_output(list_current_networks_command, shell=True, text=True)
			str_n_out = str(network_output)
			start_idx = str_n_out.find('wifi') + 10

			if not str_n_out[start_idx] == 'c':
				sys.exit('Not connected to Wifi')

			Wifi_SSID = ''
			for i in range(start_idx + 24, len(str_n_out)):
				if str_n_out[i] == '\n':
					Wifi_SSID = Wifi_SSID.replace(' ', '')
					break
				Wifi_SSID += str_n_out[i]
			
			return True, Wifi_SSID
		
		except subprocess.CalledProcessError:
			print("Network manager is not running")
			return False, 0
	else : 
		print("Unsupported OS")
		return False, 0


def model_exist () :
	if not os.path.exists('Model to Load') :
		print ('Please put the model to load in the folder')
		os.makedirs('Model to Load')
		return False
	elif len(os.listdir('./Model to Load')) < 1 :
		print ('Please put a model to load in the folder')
		return False
	else :
		for i, _ in enumerate(os.listdir('./Model to Load')) :
			if not os.listdir('./Model to Load')[i].endswith(('.pt','.pth')) :
				print('Please put a valid file in the folder')
				return False
		return os.listdir('./Model to Load')


def format_time(time_in_s) :
	time_h = time_in_s//3600
	time_m = time_in_s%3600//60
	time_s = time_in_s%60

	if time_h != 0:
		return "{}h {}min {}s".format(round(time_h), round(time_m), round(time_s))
	elif time_m != 0:
		return "{}min {}s".format(round(time_m), round(time_s))
	else:
		return "{}s".format(round(time_s))

def plot_confusion_matrix (ConfusionMatrix, ActionNames, path_to_save, Show=False) :
	plt.close()
	plt.figure(figsize=(6, 6))
	sns.heatmap(ConfusionMatrix, annot=True, fmt="d", cmap="Blues", cbar=False, xticklabels=ActionNames.keys(), yticklabels=ActionNames.keys())
	plt.xlabel('Predicted')
	plt.ylabel('Actual')
	plt.title('Confusion Matrix')
	plt.savefig(path_to_save + '/Transparent Graphs/Confusion Matrix_Transparent.png', transparent=True)
	plt.savefig(path_to_save + '/Confusion Matrix.png', transparent=False)
	if Show :
		plt.show()

def plot_precision_recall_curve (all_labels, all_scores, ActionNames, path_to_save, Show = False) :
	plt.close()
	for i, class_name in enumerate(ActionNames.keys()):
		precision, recall, _ = precision_recall_curve(all_labels == i, all_scores[:, i])
		plt.plot(recall, precision, lw=2, label=f'{class_name}')

	plt.title('Precision-Recall Curve')
	plt.xlabel('Recall')
	plt.ylabel('Precision')
	plt.legend(loc='best', shadow=True)  # Use 'best' location for the legend
	plt.grid(True)
	plt.savefig(path_to_save+'/Transparent Graphs/Precision-Recall Curve_Transparent.png', transparent=True)
	plt.savefig(path_to_save+'/Precision-Recall Curve.png', transparent=False)
	if Show :
		plt.show()

def plot_f1_score(all_labels, all_scores, ActionNames, path_to_save, Show=False):
	stats = precision_recall_fscore_support(all_labels, all_scores)
	macro = precision_recall_fscore_support(all_labels, all_scores, average='macro')
	weighted = precision_recall_fscore_support(all_labels, all_scores, average='weighted')
	accuracy = accuracy_score(all_labels, all_scores)
	precision = stats[0]
	recall = stats[1]
	fscore = stats[2]
	support = stats[3]
	total = 0
	for i in range(len(support)):
		total += support[i].item()

	final = [("Action", "Precision", "Recall", "F1-score", "Support")]
	for i in range(len(list(ActionNames.keys()))):
		final.append((list(ActionNames.keys())[i], precision[i].item(), recall[i].item(), fscore[i].item(), support[i].item()))
	final.append(("Accuracy", "", "", accuracy, total))
	final.append(("Macro Avg", macro[0].item(), macro[1].item(), macro[2].item(), total))
	final.append(("Weighted Avg", weighted[0].item(), weighted[1].item(), weighted[2].item(), total))

	# Create csv to store model training performances
	with open(path_to_save+"/F1-score.csv", "w", newline="") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerows(final)

	if Show:
		print(classification_report(all_labels, all_scores, target_names = ActionNames))

def plot_training_performances(LossTrainingTracking, LossValidationTracking, AccuracyTrainingTracking, AccuracyValidationTracking, path_to_save, num_epochs, Show = False):
	if num_epochs == 1 :
		num_epochs = 2

	plt.close()
	fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
	fig.suptitle("NN Training Performances")

	ax1.plot(LossTrainingTracking, '.-', label='Training Loss')
	ax1.plot(LossValidationTracking, '.-', label='Validation Loss')
	ax1.legend()
	ax1.set_title('Loss over Epochs')
	ax1.set_xlim(0, num_epochs-1)
	ax1.set_ylim(0, 1)
	ax1.set_ylabel("Loss")

	ax2.plot(AccuracyTrainingTracking, '.-', label='Training Accuracy')
	ax2.plot(AccuracyValidationTracking, '.-', label='Validation Accuracy')
	ax2.legend()
	ax2.set_title('Accuracy over Epochs')
	ax2.set_xlim(0, num_epochs-1)
	ax2.set_ylim(0, 100)
	ax2.set_xlabel("Epoch")
	ax2.set_ylabel("Accuracy")

	plt.savefig(path_to_save+'/Transparent Graphs/NN Training Performances_Transparent.png', transparent=True)
	plt.savefig(path_to_save+'/NN Training Performances.png', transparent=False)
	if Show :
		plt.show()



def ask_yn(question='(Y/N)') :
	ask = input(question)
	for _ in range(5) :
		if ask.upper() == "Y" or ask.upper() == "YES" :
			return True
		elif ask.upper() == "N" or ask.upper() == "NO" :
			return False
		else : ask = str(input('Yes or No :'))
	sys.exit(1)




