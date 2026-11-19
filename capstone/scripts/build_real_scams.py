"""Builds data/real_world_scams.csv: real scam SMS reported by recipients in public sources.
Only messages explicitly reported as SMS actually received, copied as published. No message is invented or rewritten."""
import csv, sys

SA = "https://www.signal-arnaques.com/scam/view/"
FA = "https://forum-assures.ameli.fr/questions/"
rows = [
# category, text, source, date reported (as published), note
("colis", "Bonjour, je n'ai pas reussi a deposer votre colis dans la boite aux lettres, merci de selectionner un creneau Sur https://chronopost.pickup-suivi.com", SA+"742352", "2024-02-19", ""),
("colis", "Nous avons essayé de livrer votre colis mais il n'y a aucun affranchissement. Suivez les instructions https://prdtlnk.com/OtPImXK", SA+"192442", "", ""),
("colis", "Bonjour c'est le livreur, votre colis ne rentre pas dans la boîte aux lettres, reprogrammez la livraison via", "https://www.clubic.com/actualite-563448-alerte-reprogrammez-la-livraison-les-arnaques-au-colis-par-sms-continuent-encore-et-encore-attention.html", "", "URL removed and one typo corrected by the journalist"),
("amende", "ANTAI: Vous avez un retard de paiement d'une infraction routière, dernier rappel avant majoration. Réf Dossier: 108470 Consulter mon dossier d'infraction via: https://amende-finances.fr", SA+"625854", "2023-03", ""),
("amende", "AMENDE GOUV : Dernier rappel avant majoration de 135 euros. dossier référence321457.Consultez votre dossier pénal sur : https://infospenalite.com", SA+"679801", "2023-08-23", ""),
("amende", "INFO ANTAI : Vous avez un retard paiement de 35,00 Euros. Consulter votre dossier d'infraction via : https://amendes-secures-gouvs.com", SA+"679844", "2023-08", ""),
("amende", "Info ANTAI : Vous avez un retard de paiement de 135,00 €. Référence : 3145. consulter mon dossier d'infraction via : paiement-antai.com", SA+"625625", "2023-03", ""),
("amende", "INFO ANTAI : Vous avez un retard de paiement de 35.00€ Dossier référence 36780923. Consulter mon dossier d'infraction via : https://antai-telepaiment.com/", SA+"149169", "2023-12", ""),
("amende", "Info ANTAI : Vous avez un retard de paiement de 35,00e, consulter mon dossier d'infraction via : https://reglements-contraventions-paiement.com", SA+"149169", "2023-12-04", ""),
("amende", "Merci de régler la situation avant le 23 Aout sous peine d'une majoration pouvant atteindre jusqu'à 135 euros. Consulter votre dossier ANTAI via : https://mes-amendes-gouv-fr.com/", SA+"679708", "2023-08", "beginning of the message may be missing"),
("amende", "Merci de régler la situation avant le 29 Septembre sous peine d'une majoration pouvant atteindre jusqu'à 135 euros. Consulter votre dossier ANTAI via : https://amende-antai-gouv-fr.com", SA+"679801", "2023-09-10", "beginning of the message may be missing"),
("ameli", "Ameli : Afin de continuer à être couvert par votre carte vitale, remplissez ce formulaire en suivant ce lien : https://ameli-vitale.com/", FA+"2861962-sms-frauduleux/answers/7375191", "", ""),
("ameli", "Expiration de votre carte vitale, à mettre à jour impérativement en suivant le lien ci-dessous : ameli-frr.com.", FA+"2876309-recu-sms-demande-ameli-mettre-jour-informations/answers/7422936", "", ""),
("ameli", "Ameli : Pour mettre votre carte vitale a jour nous vous prions de remplir ce dossier sous 48 heures. https://vital-assurance-maladie.com", FA+"2913960-sms-frauduleux", "", ""),
("ameli", "Votre nouvelle carte vitale est disponible sur votre espace client Ameli. Veuillez confirmer vos informations sur : https://ameli.smsb.co/2L9Vkq", FA+"2908573-sms-frauduleux", "", ""),
("ameli", "Votre nouvelle carte de santé est disponible, veuillez remplir le formulaire d'envoi: mon-portail-vitale.com/sante", FA+"2908573-sms-frauduleux", "", ""),
("ameli", "Votre nouvelle carte vitale est disponible. Veuillez remplir le formulaire afin de continuer a etre couvert : ameli-secu.fr.", FA+"2937275-sms-frauduleux", "", ""),
("ameli", "Votre nouvelle carte vitale est disponible. Veuillez remplir le formulaire afin de continuer a etre couvert : ameli-renouvellement.fr", FA+"2254613-sms-recu-ameli-frauduleux", "", ""),
("ameli", "Votre nouvelle carte vitale est disponible. Veuillez remplir le formulaire afin de rester couvert: infor-ameli.com", FA+"2912229-sms-frauduleux-07-45-71-59-30", "", ""),
("ameli", "Assurance Maladie: Expiration de votre carte vitale, Veuillez impérativement mettre à jour votre dossier avant le 20/08 via : Secure-macartevitale.fr", FA+"2842320-sms-frauduleux/answers/7313301", "", ""),
("ameli", "Assurance Maladie : Expiration de votre carte vitale, à mettre à jour impérativement. Ci-dessous : ameli-sms.com", FA+"2928866-sms-frauduleux/answers/7610415", "", ""),
("ameli", "Votre nouvelle carte vitale est disponible. Veuillez remplir le formulaire afin de continuer à être couvert via ameli-vital.fr.", FA+"2855333-sms-frauduleux", "", ""),
("ameli", "Ameli.fr : Dernière relance avant suspension temporaire de vos droits à la sécurité sociale Mise à jour via : https://actualisation-service-assure-enligne.com/", FA+"3531269-sms-frauduleux", "", ""),
("ameli", "Mr/Mme Dernière relance avant suspension temporaire de vos droits au remboursement de la sécurité sociale AMELI. Le renouvellement de votre carte vitale est disponible des à présent sur l'espace client", FA+"3289770-sms-frauduleux", "2024-01", "end of the message (link) not published"),
("cpf", "Votre solde cpf 2022 a été mis jour. Consultez et convertissez vos droits formation de 2021 des maintenant https://infoscpf.typeform.com/eligibilite10", SA+"434570", "2022-01-03", ""),
("cpf", "Veuillez mettre à jour votre statut avant le 1/02/2022 et actualiser ci après vos droits pour l'année 2022 https://mon-cpf.typeform.com/infos", SA+"451670", "2022-02-01", ""),
("cpf", "Votre budget CPF de 2021 arrive à expiration. Il vous reste 48h pour mettre à jour vos droits de 2022 : https://format-france.typeform.com/infos", SA+"448290", "2022-02", ""),
("cpf", "Votre budget C-P-F de 2021 arrive a expiration. Il vous reste 48h pour mettre a jour vos droits de 2022: https://france-format.typeform.com/infos", SA+"448290", "2022-02", ""),
("cpf", "M L***, vous disposez de droits formation inutilisés. https://pws.ms/PIHIP", SA+"419652", "2021-12-21", "name masked by the reporter"),
("cpf", "Votre solde C.P.F, de 2022 est a jour. Il vous reste 48h pour consulter et convertir vos droits formation de 2021: https://mon-cpf.typeform.com/infos", SA+"443780", "2022-01-16", ""),
("cpf", "Votre solde C.P.F 2022 est à jour (+320 Euros). Vérifiez et utilisez cos droits avant expiration ! LIEN: https://droits.typeform.com/to/dyl0eqPh", SA+"443780", "2022-01-28", ""),
("cpf", "votre solde C.P.F 2022 est a jour. Merci de consulter et Activer vos droits des maintenant https://droits2.info/LHvHrT", SA+"468560", "2022-03-15", ""),
("cpf", "Votre solde C.P.F 2022 est à jour (+500 Euros). Vérifiez et utilisez vos droits avant expiration ! Sur https://bit.ly/typesolde-cpf", SA+"481566", "2022", ""),
("cpf", "Votre compte CPF arrive a expiration. Veuillez remplir le formulaire ci-dessous sous 24h, pour covertir vos droits 2021. https://cpforma.typeform.com/droit", SA+"441144", "2022-03", ""),
("famille", "Bonjour Maman, j'ai laissé tomber mon téléphone dans les toilettes, voici mon nouveau numéro 0745158119. tu peux m'envoyer un message sur whatsApp", SA+"747293", "2024-03-07", ""),
("famille", "coucou maman je viens de casser mon téléphone pouvez-vous m'envoyer un message sur mon nouveau numéro c'est 33756945791", SA+"742756", "2024-02-21", ""),
("famille", "Coucou maman, c'est moi. J'ai eu un problème avec mon numéro de téléphone, c'est mon numéro temporaire. Envoie-moi un message sur WhatsApp, sur ce numéro, le plus rapidement possible.", "https://www.universfreebox.com/article/563199/une-arnaque-par-sms-en-vogue-sevit-en-france", "", "example published by the French Interior Ministry spokesperson"),
("banque", "Ceci est un message de votre banque : vous avez une opération en cours sur votre carte de débit, si ce n'est pas vous, veuillez immédiatement faire opposition en appelant le numéro de CardStop au 071 350 499", SA+"902630", "2026-02", "received in Belgium"),
("banque", "Votre achat de 1350.90 EUR à bien été effectué. Si vous n'etes pas à l'origine de cette opération, appelez le 0176502502 (numéro non surtaxé", SA+"708733", "2021-04-24", "end of message cut in the source"),
]

out = sys.argv[1]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["text", "label", "category", "language", "source_url", "reported", "note"])
    for cat, text, src, date, note in rows:
        w.writerow([text, "spam", cat, "fr", src, date, note])
print(len(rows), "messages written to", out)
