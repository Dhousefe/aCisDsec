package net.sf.l2j.gameserver.util;

import java.io.FileInputStream;
import java.util.List;
import java.util.Properties;

import net.sf.l2j.gameserver.skills.L2Skill;
import net.sf.l2j.gameserver.model.actor.Player;

public class SpecialModCancelRestore {

    public static boolean CANCEL_RESTORE = false;
    public static int CUSTOM_CANCEL_TASK_DELAY = 10000; // valor padrão: 10 segundos

    static {
        try {
            Properties props = new Properties();
            props.load(new FileInputStream("config/CustomMods/SpecialMods.ini"));
            CANCEL_RESTORE = Boolean.parseBoolean(props.getProperty("CancelRestore", "false"));
            CUSTOM_CANCEL_TASK_DELAY = Integer.parseInt(props.getProperty("CustomCancelTaskDelay", "10000"));
        } catch (Exception e) {
            System.err.println("Erro ao carregar CancelRestore/CustomCancelTaskDelay do SpecialMods.ini: " + e.getMessage());
        }

        // Print estiloso ao ligar o servidor
        System.out.println("===============================================");
        System.out.println("   [SpecialModCancelRestore] Status do Mod:");
        System.out.println("   CancelRestore.............: " + (CANCEL_RESTORE ? "ATIVADO" : "DESATIVADO"));
        System.out.println("   CustomCancelTaskDelay.....: " + CUSTOM_CANCEL_TASK_DELAY + " ms");
        System.out.println("===============================================");
    }

    /**
     * Agenda a restauração dos buffs cancelados para o player após o delay configurado.
     */
    public static void scheduleBuffRestore(Player player, List<L2Skill> buffsCanceled) {
        if (player == null || buffsCanceled == null || buffsCanceled.isEmpty())
            return;

        net.sf.l2j.commons.pool.ThreadPool.schedule(
            () -> restoreBuffs(player, buffsCanceled),
            CUSTOM_CANCEL_TASK_DELAY
        );
    }

    /**
     * Restaura os buffs cancelados no player.
     */
    private static void restoreBuffs(Player player, List<L2Skill> buffsCanceled) {
        if (player == null || player.isDead() || !player.isOnline())
            return;

        for (L2Skill skill : buffsCanceled) {
            if (skill == null)
                continue;

            // Evita reaplicar se já estiver ativo
            if (player.getFirstEffect(skill.getId()) != null)
                continue;

            skill.getEffects(player, player);

            // Toca um som para o jogador ao restaurar o buff
            player.sendPacket(new net.sf.l2j.gameserver.network.serverpackets.PlaySound("ItemSound.quest_middle"));
            //System.out.println("[CancelRestore] Buff restaurado: " + skill.getName() + " para " + player.getName());
        }
    }
}