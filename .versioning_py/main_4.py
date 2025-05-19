import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class ExcelAnalyzer:
    def __init__(self):
        self.df = None
        self.verif_col = 'Verivikasi Pengawas'  # Sesuaikan jika perlu
        self.category_col = None
        self.selected_verif = None
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
        combined_df = pd.concat(dfs, ignore_index=True, sort=True)  # sort=True agar kolom berbeda juga tercakup
        return combined_df

    def get_columns(self):
        if self.df is None:
            return [], []
        num_cols = self.df.select_dtypes(include='number').columns.tolist()
        cat_cols = self.df.select_dtypes(include='object').columns.tolist()
        return num_cols, cat_cols

    def filter_and_group(self):
        if self.df is None or self.category_col is None or self.selected_verif is None:
            return pd.DataFrame()
        if self.verif_col not in self.df.columns:
            return pd.DataFrame()

        filtered = self.df[self.df[self.verif_col] == self.selected_verif]
        grouped = filtered[self.category_col].value_counts().reset_index()
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
    st.title("📊 Excel Analyzer - Gabungkan Multi File & Sheet")

    analyzer = ExcelAnalyzer()

    st.sidebar.header("📥 Upload & Pilih Parameter")

    uploaded_files = st.sidebar.file_uploader(
        "Upload satu atau beberapa file Excel (.xlsx)",
        type=['xlsx'], accept_multiple_files=True)

    if uploaded_files:
        # Ambil semua nama sheet unik dari semua file
        sheets = analyzer.get_all_sheet_names(uploaded_files)
        if not sheets:
            st.warning("Tidak ada sheet ditemukan di file yang diupload.")
            return

        sheet_choice = st.sidebar.selectbox("Pilih sheet yang akan digabung dari semua file", sheets)

        # Load dan gabungkan semua sheet yang dipilih dari tiap file
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
        analyzer.selected_verif = st.sidebar.selectbox(f"Pilih Kondisi '{analyzer.verif_col}'", verif_options)

        analyzer.top_n = st.sidebar.slider("Pilih Top N kategori untuk ditampilkan", min_value=1, max_value=100, value=10)

        grouped = analyzer.filter_and_group()
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
            return

        analyzer.plot_bar(grouped)

        st.write("### 📋 Tabel Detail")
        st.dataframe(grouped)

if __name__ == "__main__":
    main()
