import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class ExcelAnalyzer:
    def __init__(self):
        self.df = None
        self.sheet_names = []
        self.category_col = None
        self.verif_col = 'Verivikasi Pengawas'  # Bisa disesuaikan
        self.selected_verif = None
        self.top_n = 10

    def get_sheet_names_from_all_files(self, uploaded_files):
        # Kumpulkan sheet names dari semua file
        all_sheets = set()
        for f in uploaded_files:
            try:
                xls = pd.ExcelFile(f)
                all_sheets.update(xls.sheet_names)
            except Exception as e:
                st.warning(f"Gagal membaca file {f.name}: {e}")
        return sorted(all_sheets)

    def load_and_merge_sheets(self, uploaded_files, sheet_name):
        # Load sheet tertentu dari setiap file, gabungkan secara union, handle kolom berbeda
        df_list = []
        for f in uploaded_files:
            try:
                xls = pd.ExcelFile(f)
                # Jika sheet ada di file, baca, kalau tidak, skip file itu
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    df_list.append(df)
                else:
                    st.warning(f"File {f.name} tidak memiliki sheet '{sheet_name}', dilewati.")
            except Exception as e:
                st.warning(f"Gagal membaca sheet '{sheet_name}' di file {f.name}: {e}")
        if not df_list:
            return None
        # Gabungkan dengan union (outer join kolom)
        merged_df = pd.concat(df_list, ignore_index=True, sort=True)
        return merged_df

    def get_columns(self):
        if self.df is None:
            return [], []
        num_cols = self.df.select_dtypes(include='number').columns.tolist()
        cat_cols = self.df.select_dtypes(include='object').columns.tolist()
        return num_cols, cat_cols

    def filter_and_group(self):
        if self.df is None or self.category_col is None or self.selected_verif is None:
            return pd.DataFrame()

        # Jika kolom verif_col tidak ada, return empty
        if self.verif_col not in self.df.columns:
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
    st.title("📊 Excel Data Analyzer with Streamlit (Multi File & Sheet)")

    analyzer = ExcelAnalyzer()

    st.sidebar.header("📥 Upload & Pilih Parameter")

    uploaded_files = st.sidebar.file_uploader(
        "Upload satu atau beberapa file Excel (.xlsx)",
        type=['xlsx'], accept_multiple_files=True)

    if uploaded_files and len(uploaded_files) > 0:
        # 1. Dapatkan semua sheet unik dari semua file
        all_sheets = analyzer.get_sheet_names_from_all_files(uploaded_files)
        if not all_sheets:
            st.warning("Tidak ada sheet yang bisa dibaca dari file yang diupload.")
            return

        # 2. Pilih sheet yang ingin dipakai (harus sama di semua file)
        sheet_to_use = st.sidebar.selectbox("Pilih Sheet yang akan digabung dari semua file", all_sheets)

        # 3. Load dan merge sheet tersebut dari semua file
        merged_df = analyzer.load_and_merge_sheets(uploaded_files, sheet_to_use)

        if merged_df is None or merged_df.empty:
            st.warning("Gagal menggabungkan data dari file yang diupload.")
            return

        analyzer.df = merged_df

        # 4. Tampilkan info kolom
        num_cols, cat_cols = analyzer.get_columns()
        st.sidebar.markdown(f"**Kolom Numerik:** {', '.join(num_cols) if num_cols else 'Tidak ada'}")
        st.sidebar.markdown(f"**Kolom Kategorikal:** {', '.join(cat_cols) if cat_cols else 'Tidak ada'}")

        if len(cat_cols) == 0:
            st.warning("Data gabungan tidak memiliki kolom kategorikal untuk analisis.")
            return

        # 5. Pilih kolom kategori
        analyzer.category_col = st.sidebar.selectbox("Pilih Kolom Kategori untuk Analisis", cat_cols)

        # 6. Pastikan kolom verif ada
        if analyzer.verif_col not in analyzer.df.columns:
            st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
            return

        # 7. Pilih kondisi verifikasi
        verif_values = analyzer.df[analyzer.verif_col].dropna().unique().tolist()
        analyzer.selected_verif = st.sidebar.selectbox(f"Pilih Kondisi dari '{analyzer.verif_col}'", verif_values)

        # 8. Pilih top N
        analyzer.top_n = st.sidebar.slider("Pilih jumlah Top N kategori yang ingin ditampilkan", 1, 100, 10)

        # 9. Filter dan group
        grouped = analyzer.filter_and_group()
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
            return

        # 10. Visualisasi
        analyzer.plot_bar(grouped)

        # 11. Tampilkan tabel detail
        st.write("### 📋 Tabel Detail")
        st.dataframe(grouped)

if __name__ == "__main__":
    main()
