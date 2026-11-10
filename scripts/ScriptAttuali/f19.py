# Prepara DYNAMITE_DISPOSAL_SPECIALIST: serve uno strato di dinamite a -600 z o piu' giu',
# su campo 32x32. Ogni esecuzione salta allo strato di dinamite SUCCESSIVO.
# Eseguilo piu' volte (senza clear() e senza cambiare dimensione del campo)
# finche' stampa z <= -600. Poi lancia il tuo risolutore f12 TOGLIENDO la riga
# clear() che c'e' prima di jump(Unlocks.Dynamite): saltera' a uno strato ancora piu' giu'.


jump(Unlocks.Dynamite)
quick_print("strato di dinamite vicino a z", get_pos_z(), "- campo", get_world_size())
