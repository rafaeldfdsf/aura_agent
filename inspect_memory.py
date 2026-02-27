#!/usr/bin/env python3
"""
Script para inspecionar a memória SQLite do agente Darian
"""
import sqlite3
import os
from datetime import datetime

DB_FILE = "darian_memory.db"

def inspect_memory():
    if not os.path.exists(DB_FILE):
        print(f"❌ Base de dados '{DB_FILE}' não encontrada!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 INSPEÇÃO DE MEMÓRIA - DARIAN AGENT")
    print("="*60 + "\n")
    
    # === USER DATA ===
    print("👤 DADOS DO UTILIZADOR:")
    print("-" * 60)
    cursor.execute("SELECT * FROM user_data")
    user = cursor.fetchone()
    if user:
        print(f"  Summary length: {len(user['summary'])} caracteres")
        print(f"  Created: {user['created_at']}")
        print(f"  Updated: {user['updated_at']}")
        if user['summary']:
            print(f"\n  📝 Resumo:\n  {user['summary']}\n")
        else:
            print("  ⚠️  Nenhum resumo consolidado ainda.\n")
    
    # === MESSAGES ===
    print("💬 HISTÓRICO DE MENSAGENS:")
    print("-" * 60)
    cursor.execute("SELECT COUNT(*) FROM messages")
    total = cursor.fetchone()[0]
    print(f"  Total de mensagens: {total}\n")
    
    # Últimas 6 mensagens
    cursor.execute("""
        SELECT role, content, created_at 
        FROM messages 
        ORDER BY id DESC 
        LIMIT 6
    """)
    messages = cursor.fetchall()
    
    if messages:
        print("  Últimas 6 mensagens (mais recentes primeiro):")
        print("  " + "-" * 56)
        for i, msg in enumerate(reversed(messages), 1):
            role = "👨 Utilizador" if msg['role'] == 'user' else "🤖 Darian"
            text = msg['content'][:50].replace("\n", " ")
            if len(msg['content']) > 50:
                text += "..."
            print(f"  {i}. [{role}] {text}")
    else:
        print("  ⚠️  Sem mensagens guardadas.")
    
    # === ESTATÍSTICAS ===
    print("\n📈 ESTATÍSTICAS:")
    print("-" * 60)
    cursor.execute("""
        SELECT role, COUNT(*) as count 
        FROM messages 
        GROUP BY role
    """)
    stats = cursor.fetchall()
    
    for stat in stats:
        role_label = "Utilizador" if stat['role'] == 'user' else "Darian"
        print(f"  {role_label}: {stat['count']} mensagens")
    
    # === CONSOLIDAÇÃO STATUS ===
    print("\n🧠 STATUS DE CONSOLIDAÇÃO:")
    print("-" * 60)
    max_messages = 8
    consolidate_threshold = max_messages
    print(f"  Limiar de consolidação: {consolidate_threshold} mensagens")
    print(f"  Mensagens atuais: {total}")
    
    if total > consolidate_threshold:
        print(f"  ✅ PRONTO para consolidação ({total} > {consolidate_threshold})")
    else:
        print(f"  ⏳ Aguardando consolidação ({total}/{consolidate_threshold})")
    
    # Verifica se há resumo
    if user and user['summary']:
        print(f"  ✅ Resumo já consolidado")
    else:
        print(f"  ⏳ Aguardando primeiro resumo")
    
    conn.close()
    print("\n" + "="*60 + "\n")

def clear_memory():
    """Limpa toda a memória (uso para testes)"""
    if not os.path.exists(DB_FILE):
        print(f"Base de dados '{DB_FILE}' não encontrada!")
        return
    
    confirm = input("⚠️  Tem a certeza que quer limpar TODA a memória? (s/n): ").lower()
    if confirm == 's':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("UPDATE user_data SET summary = ''")
        conn.commit()
        conn.close()
        print("✅ Memória limpa!")
    else:
        print("Cancelado.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        clear_memory()
    else:
        inspect_memory()
