import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

class ExcelAnalyzer:
    def __init__(self):
        # Ubah jika kolom di file Excel Anda adalah 'Verifikasi Pengawas'
        self.verif_col = 'Verivikasi Pengawas'  
        self.df = None
        self.category_col = None
        self.selected_verif = []
        self.top_n = 10

    def get_all_sheet_names(self, files):
        sheets = set()
        for f in files:
            try:
                xls = pd.ExcelFile(f)
                sheets.update(xls.sheet_names)
            except Exception as e:
                st.warning(f"Gagal baca file {f.name}: {e}")
        return sorted(list(sheets))

    def load_and_concat_sheets(self, files, sheet_name):
        dfs = []
        for f in files:
            try:
                xls = pd.ExcelFile(f)
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    df['filename'] = f.name  # Tambahkan kolom nama file
                    dfs.append(df)
                else:
                    st.warning(f"File {f.name} tidak punya sheet '{sheet_name}', dilewati.")
            except Exception as e:
                st.warning(f"Gagal baca sheet '{sheet_name}' di file {f.name}: {e}")
        if not dfs:
            return None
        combined_df = pd.concat(dfs, ignore_index=True, sort=True)
        return combined_df


    def get_columns(self):
        if self.df is None:
            return [], []
        num_cols = self.df.select_dtypes(include='number').columns.tolist()
        cat_cols = self.df.select_dtypes(include='object').columns.tolist()
        return num_cols, cat_cols

    def filter_and_group(self):
        if self.df is None or self.category_col is None or not self.selected_verif:
            return pd.DataFrame()
        if self.verif_col not in self.df.columns:
            return pd.DataFrame()

        filtered = self.df[self.df[self.verif_col].isin(self.selected_verif)]

        grouped = filtered[self.category_col].value_counts().reset_index()
        grouped.columns = [self.category_col, 'Jumlah']
        grouped['Jumlah'] = grouped['Jumlah'].astype(int)
        grouped = grouped.head(self.top_n)
        return grouped

    def plot_bar(self, grouped):
        plt.figure(figsize=(10, 6))
        barplot = sns.barplot(data=grouped, x='Jumlah', y=self.category_col, palette='mako')
        selected_str = ", ".join(map(str, self.selected_verif))
        plt.title(f"Top {self.top_n} untuk kondisi [{selected_str}] berdasarkan '{self.category_col}'")
        plt.xlabel("Jumlah")
        plt.ylabel(self.category_col)

        plt.gca().xaxis.get_major_formatter().set_scientific(False)
        plt.gca().xaxis.get_major_formatter().set_useOffset(False)
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}'))

        for i, value in enumerate(grouped['Jumlah']):
            barplot.text(value + 0.5, i, str(value), color='black', va='center')

        plt.tight_layout()
        st.pyplot(plt.gcf())
        plt.close()

    def calculate_confusion_stats(self):
        """
        Hitung statistik verifikasi per file (TP, TN, FP, FN, Total, Accuracy, dll).
        Return: df_counts_with_filename, df_metrics_with_filename
        """
        if self.df is None or self.verif_col not in self.df.columns or 'filename' not in self.df.columns:
            return None, None

        count_rows_perfile = []
        metric_rows_perfile = []
        count_rows_total = []
        metric_rows_total = []

        for filename, group in self.df.groupby("Key"):
            counts = group[self.verif_col].value_counts()
            TP = counts.get('True Positive', 0)
            TN = counts.get('True Negative', 0)
            FP = counts.get('False Positive', 0)
            FN = counts.get('False Negative', 0)
            total = TP + TN + FP + FN

            accuracy = (TP + TN) / total if total else None
            recall = TP / (TP + FN) if (TP + FN) else None
            precision = TP / (TP + FP) if (TP + FP) else None
            f1_score = (2 * precision * recall) / (precision + recall) if (precision and recall and (precision + recall)) else None

            count_rows_perfile.append({
                'filename': filename[:4],
                'year': filename[5:9],
                'type' : filename[10:],
                'TP': TP, 'TN': TN, 'FP': FP, 'FN': FN, 'Total': total
            })
            metric_rows_perfile.append({
                'filename': filename[:4],
                'year': filename[5:9],
                'type' : filename[10:],
                'Accuracy': accuracy,
                'Recall': recall,
                'Precision': precision,
                'F1 Score': f1_score
            })

        for filename, group in self.df.groupby("filename"):
            counts = group[self.verif_col].value_counts()
            TP = counts.get('True Positive', 0)
            TN = counts.get('True Negative', 0)
            FP = counts.get('False Positive', 0)
            FN = counts.get('False Negative', 0)
            total = TP + TN + FP + FN

            accuracy = (TP + TN) / total if total else None
            recall = TP / (TP + FN) if (TP + FN) else None
            precision = TP / (TP + FP) if (TP + FP) else None
            f1_score = (2 * precision * recall) / (precision + recall) if (precision and recall and (precision + recall)) else None

            count_rows_total.append({
                '' : 'Total',    
                'TP': TP, 'TN': TN, 'FP': FP, 'FN': FN, 'Total': total
            })
            metric_rows_total.append({
                '': 'Total',
                'Accuracy': accuracy,
                'Recall': recall,
                'Precision': precision,
                'F1 Score': f1_score
            })

        df_counts = pd.DataFrame(count_rows_perfile)
        df_metrics = pd.DataFrame(metric_rows_perfile)
        df_counts_total = pd.DataFrame(count_rows_total)
        df_metrics_total = pd.DataFrame(metric_rows_total)
        return df_counts, df_metrics, df_counts_total, df_metrics_total
