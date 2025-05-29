package net.sf.l2j.gameserver.model.enums;

public enum AttackType
{
    Normal(0),
    Magic(1),
    Crit(2),
    MCrit(3),
    Blow(4),
    PhysicalSkillDamage(5),
    PhysicalSkillCritical(6);
	
	private int _attackId;
	public static final AttackType[] VALUES = values();
	
	private AttackType(int attackId)
	{
		_attackId = attackId;
	}
	
	public int getId()
	{
		return _attackId;
	}
}