import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class ExcelAnalyzer:
    def __init__(self):
        self.df = None
        self.verif_col = 'Verivikasi Pengawas'  # Sesuaikan jika perlu
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
        plt.clf()

    def calculate_confusion_stats(self):
        """
        Menghitung TP, TN, FP, FN, Total serta Accuracy, Recall, Precision, F1 Score 
        berdasarkan kolom self.verif_col yang harus mengandung nilai "TP", "TN", "FP", "FN".
        """
        if self.df is None or self.verif_col not in self.df.columns:
            return None, None
        
        counts = self.df[self.verif_col].value_counts()
        # Ambil nilai default 0 jika tidak ada
        TP = counts.get('True Positive', 0)
        TN = counts.get('True Negative', 0)
        FP = counts.get('False Positive', 0)
        FN = counts.get('False Negative', 0)
        total = TP + TN + FP + FN

        # Hitung metrics, jaga agar tidak div0
        accuracy = (TP + TN) / total if total else None
        recall = TP / (TP + FN) if (TP + FN) else None
        precision = TP / (TP + FP) if (TP + FP) else None
        f1_score = (2 * precision * recall) / (precision + recall) if (precision and recall and (precision + recall)) else None

        # Dataframe tabel counts
        df_counts = pd.DataFrame({
            'Key': ['TP', 'TN', 'FP', 'FN', 'Total'],
            'Count': [TP, TN, FP, FN, total]
        })

        # Dataframe metrics
        df_metrics = pd.DataFrame({
            'Key': ['Accuracy', 'Recall', 'Precision', 'F1 Score'],
            'Value': [accuracy, recall, precision, f1_score]
        })

        return df_counts, df_metrics

def main():
    st.title("📊 Excel Analyzer dengan Tabs")

    analyzer = ExcelAnalyzer()

    st.sidebar.header("📥 Upload & Pilih Parameter")

    uploaded_files = st.sidebar.file_uploader(
        "Upload satu atau beberapa file Excel (.xlsx)",
        type=['xlsx'], accept_multiple_files=True)

    if not uploaded_files:
        st.info("Silakan upload minimal satu file Excel (.xlsx) di sidebar.")
        return

    sheets = analyzer.get_all_sheet_names(uploaded_files)
    if not sheets:
        st.warning("Tidak ada sheet ditemukan di file yang diupload.")
        return

    sheet_choice = st.sidebar.selectbox("Pilih sheet yang akan digabung dari semua file", sheets)

    combined_df = analyzer.load_and_concat_sheets(uploaded_files, sheet_choice)
    if combined_df is None or combined_df.empty:
        st.warning("Data gabungan kosong atau gagal dibaca.")
        return

    analyzer.df = combined_df

    num_cols, cat_cols = analyzer.get_columns()
    st.sidebar.markdown(f"**Kolom Numerik:** {', '.join(num_cols) if num_cols else 'Tidak ada'}")
    st.sidebar.markdown(f"**Kolom Kategorikal:** {', '.join(cat_cols) if cat_cols else 'Tidak ada'}")

    if len(cat_cols) == 0:
        st.warning("Data gabungan tidak memiliki kolom kategorikal untuk analisis.")
        return

    analyzer.category_col = st.sidebar.selectbox("Pilih Kolom Kategori untuk Analisis", cat_cols)

    if analyzer.verif_col not in analyzer.df.columns:
        st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
        return

    verif_options = analyzer.df[analyzer.verif_col].dropna().unique().tolist()

    # === TAB SELECTION ===
    tab1, tab2, tab3 = st.tabs(["📈 Statistik Verifikasi", "📊 Analisis Data", "📚 Dokumentasi"])

    with tab1:
        st.header("Statistik berdasarkan kolom 'Verivikasi Pengawas'")
        df_counts, df_metrics = analyzer.calculate_confusion_stats()
        if df_counts is None or df_metrics is None:
            st.warning("Data tidak mencukupi untuk menghitung statistik (pastikan kolom berisi 'True Positive', 'True Negative', 'False Positive', 'False Negative').")
        else:
            st.subheader("Jumlah Kategori")
            st.dataframe(df_counts.style.format({"Count": "{:,.0f}"}), height=200)

            st.subheader("Metrics Evaluasi")
            # Format nilai metrics ke 4 desimal jika ada
            def fmt(val):
                return f"{val:.4f}" if val is not None else "-"
            st.dataframe(df_metrics.style.format({"Value": fmt}), height=150)

    with tab2:
        st.header("Analisis Bar Chart dengan Filter Multi Verifikasi")

        analyzer.selected_verif = st.multiselect(
            f"Pilih satu atau beberapa kondisi '{analyzer.verif_col}'",
            options=verif_options,
            default=verif_options[:1]
        )

        analyzer.top_n = st.slider("Pilih Top N kategori untuk ditampilkan", min_value=1, max_value=100, value=10)

        grouped = analyzer.filter_and_group()
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
        else:
            analyzer.plot_bar(grouped)
            st.write("### 📋 Tabel Detail")
            st.dataframe(grouped)

    with tab3:
        st.header("Dokumentasi")
        st.markdown("""
        ## Panduan Penggunaan Aplikasi

        1. Upload file Excel (.xlsx) di sidebar.
        2. Pilih sheet yang ingin dianalisis.
        3. Pilih kolom kategori untuk analisis.
        4. Tab Statistik: Menampilkan jumlah dan metrik evaluasi berdasarkan kategori verifikasi.
        5. Tab Analisis Data: Menampilkan grafik dan tabel filter multi-verifikasi.
        6. Tab Dokumentasi: Informasi dan credit aplikasi.

        ---

        ## Arsitektur Aplikasi
        - Backend: Pandas untuk manipulasi data.
        - Visualisasi: Matplotlib dan Seaborn.
        - UI: Streamlit dengan Tabs.

        ---

        ## Credit
        - Dibuat oleh [Nama Anda]
        - Library:
        ## Credit
        - Dibuat oleh [Nama Anda]
        - Library: Pandas, Streamlit, Matplotlib, Seaborn
        - Terima kasih kepada komunitas open source dan dokumentasi resmi library yang digunakan.

        ---

        ## Catatan Tambahan
        - Pastikan kolom 'Verivikasi Pengawas' memiliki nilai seperti 'True Positive', 'True Negative', 'False Positive', dan 'False Negative' agar statistik bisa dihitung dengan benar.
        - Jika ada pertanyaan atau saran, silakan hubungi pengembang.

        ---
        """)

if __name__ == "__main__":
    main()