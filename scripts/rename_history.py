import os
import re

history_dir = "history"
# Padrão: boletim_ia_YYYY-MM-DD_HH-MM-SS.md
pattern = re.compile(r"boletim_ia_(\d{4})-(\d{2})-(\d{2})_(.*)\.md")

if not os.path.exists(history_dir):
    print(f"Diretório {history_dir} não encontrado.")
    exit()

renamed_count = 0
for filename in os.listdir(history_dir):
    match = pattern.match(filename)
    if match:
        year, month, day, rest = match.groups()
        new_filename = f"boletim_ia_{day}-{month}-{year}_{rest}.md"
        old_path = os.path.join(history_dir, filename)
        new_path = os.path.join(history_dir, new_filename)
        
        # Evita conflitos se já existir um com o novo nome
        if os.path.exists(new_path):
            print(f"Aviso: Ignorando {filename} (o destino {new_filename} já existe).")
            continue
            
        print(f"Renomeando: {filename} -> {new_filename}")
        os.rename(old_path, new_path)
        renamed_count += 1

print(f"\nTotal de arquivos renomeados: {renamed_count}")
