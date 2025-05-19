import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class ExcelAnalyzer:
    def __init__(self):
        self.df = None
        self.sheet_names = []
        self.selected_sheet = None
        self.category_col = None
        self.verif_col = 'Verivikasi Pengawas'  # Bisa disesuaikan
        self.selected_verif = None
        self.top_n = 10

    def load_excel(self, uploaded_file):
        # Load Excel, update sheet names
        if uploaded_file:
            self.excel_file = pd.ExcelFile(uploaded_file)
            self.sheet_names = self.excel_file.sheet_names
            return True
        return False

    def select_sheet(self, sheet_name):
        # Baca sheet ke dataframe
        self.selected_sheet = sheet_name
        self.df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
        return self.df

    def load_and_merge_multiple_files(self, uploaded_files, sheet_name=None):
        # Load dan union dataframe dari beberapa file excel
        df_list = []
        for f in uploaded_files:
            excel_file = pd.ExcelFile(f)
            # jika sheet_name tidak diberikan, pakai sheet pertama
            sheet = sheet_name if sheet_name in excel_file.sheet_names else excel_file.sheet_names[0]
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df_list.append(df)
        if df_list:
            self.df = pd.concat(df_list, ignore_index=True)
            # update sheet_names hanya untuk info, kosongkan karena gabungan
            self.sheet_names = []
            return True
        return False

    def get_columns(self):
        if self.df is None:
            return [], []
        num_cols = self.df.select_dtypes(include='number').columns.tolist()
        cat_cols = self.df.select_dtypes(include='object').columns.tolist()
        return num_cols, cat_cols

    def filter_and_group(self):
        if self.df is None or self.category_col is None or self.selected_verif is None:
            return pd.DataFrame()

        filtered_df = self.df[self.df[self.verif_col] == self.selected_verif]
        grouped = filtered_df[self.category_col].value_counts().reset_index()
        grouped.columns = [self.category_col, 'Jumlah']
        grouped['Jumlah'] = grouped['Jumlah'].astype(int)
        grouped = grouped.head(self.top_n)
        return grouped

    def plot_bar(self, grouped):
        plt.figure(figsize=(10, 6))
        barplot = sns.barplot(data=grouped, x='Jumlah', y=self.category_col, palette='mako')
        plt.title(f"Top {self.top_n} '{self.selected_verif}' berdasarkan '{self.category_col}'")
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

def main():
    st.title("📊 Excel Data Analyzer with Streamlit (OOP)")

    analyzer = ExcelAnalyzer()

    st.sidebar.header("📥 Upload & Pilih Parameter")

    # Opsi multi-upload file Excel
    uploaded_files = st.sidebar.file_uploader(
        "Upload satu atau beberapa file Excel (.xlsx)",
        type=['xlsx'], accept_multiple_files=True)

    if uploaded_files and len(uploaded_files) > 0:
        if len(uploaded_files) == 1:
            # jika cuma 1 file, pakai load_excel dan sheet selector
            loaded = analyzer.load_excel(uploaded_files[0])
            if loaded:
                sheet = st.sidebar.selectbox("Pilih Sheet", analyzer.sheet_names)
                if sheet:
                    df = analyzer.select_sheet(sheet)

                    num_cols, cat_cols = analyzer.get_columns()
                    st.sidebar.markdown(f"**Kolom Numerik:** {', '.join(num_cols) if num_cols else 'Tidak ada'}")
                    st.sidebar.markdown(f"**Kolom Kategorikal:** {', '.join(cat_cols) if cat_cols else 'Tidak ada'}")

                    if len(cat_cols) == 0:
                        st.warning("File sheet ini tidak memiliki kolom kategorikal untuk analisis.")
                        return

                    analyzer.category_col = st.sidebar.selectbox("Pilih Kolom Kategori untuk Analisis", cat_cols)

                    if analyzer.verif_col not in df.columns:
                        st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di sheet.")
                        return

                    verif_values = df[analyzer.verif_col].dropna().unique().tolist()
                    analyzer.selected_verif = st.sidebar.selectbox(f"Pilih Kondisi dari '{analyzer.verif_col}'", verif_values)

                    analyzer.top_n = st.sidebar.slider("Pilih jumlah Top N kategori yang ingin ditampilkan", 1, 100, 10)

                    grouped = analyzer.filter_and_group()
                    if grouped.empty:
                        st.info("Data tidak ditemukan untuk filter yang dipilih.")
                        return

                    analyzer.plot_bar(grouped)

                    st.write("### 📋 Tabel Detail")
                    st.dataframe(grouped)
        else:
            # Jika lebih dari 1 file, merge union dulu
            st.sidebar.info(f"Anda meng-upload {len(uploaded_files)} file, datanya akan digabung (union)")

            # Untuk opsi sheet pilih, kita ambil sheet dari file pertama sebagai default
            first_excel = pd.ExcelFile(uploaded_files[0])
            sheet_names = first_excel.sheet_names
            sheet_to_use = st.sidebar.selectbox("Pilih Sheet yang akan digabung dari semua file", sheet_names)

            merged = analyzer.load_and_merge_multiple_files(uploaded_files, sheet_to_use)

            if merged:
                num_cols, cat_cols = analyzer.get_columns()
                st.sidebar.markdown(f"**Kolom Numerik:** {', '.join(num_cols) if num_cols else 'Tidak ada'}")
                st.sidebar.markdown(f"**Kolom Kategorikal:** {', '.join(cat_cols) if cat_cols else 'Tidak ada'}")

                if len(cat_cols) == 0:
                    st.warning("Gabungan file tidak memiliki kolom kategorikal untuk analisis.")
                    return

                analyzer.category_col = st.sidebar.selectbox("Pilih Kolom Kategori untuk Analisis", cat_cols)

                if analyzer.verif_col not in analyzer.df.columns:
                    st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
                    return

                verif_values = analyzer.df[analyzer.verif_col].dropna().unique().tolist()
                analyzer.selected_verif = st.sidebar.selectbox(f"Pilih Kondisi dari '{analyzer.verif_col}'", verif_values)

                analyzer.top_n = st.sidebar.slider("Pilih jumlah Top N kategori yang ingin ditampilkan", 1, 100, 10)

                grouped = analyzer.filter_and_group()
                if grouped.empty:
                    st.info("Data tidak ditemukan untuk filter yang dipilih.")
                    return

                analyzer.plot_bar(grouped)

                st.write("### 📋 Tabel Detail")
                st.dataframe(grouped)
            else:
                st.warning("Gagal menggabungkan file Excel.")

if __name__ == "__main__":
    main()
