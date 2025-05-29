package net.sf.l2j.gameserver.data.manager;

import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

import net.sf.l2j.commons.data.xml.IXmlReader;
import net.sf.l2j.commons.data.StatSet;

import net.sf.l2j.gameserver.enums.actors.ClassId;
import net.sf.l2j.gameserver.model.actor.Creature;

import org.w3c.dom.Document;

/**
 * @author StinkyMadness
 */
public class ClassBalanceManager implements IXmlReader
{
   private final List<ClassBalanceHolder> _data = new CopyOnWriteArrayList<>();
  
   public enum ClassBalanceType
   {
       NORMAL,
       MAGIC,
       CRITICAL,
       M_CRITICAL,
       BLOW,
       PHYSICAL_SKILL_DAMAGE,
       PHYSICAL_SKILL_CRITICAL;
   }
  
   public ClassBalanceManager()
   {
       load();
   }
  
   @Override
   public void load()
   {
       parseFile("./data/xml/classBalance.xml");
       LOGGER.info("Loaded {} class balance data.", _data.size());
   }
  
   public void reload()
   {
       _data.clear();
       load();
   }
  
   @Override
   public void parseDocument(Document doc, Path path)
   {
       forEach(doc, "list", listNode -> forEach(listNode, "balance", balanceNode -> _data.add(new ClassBalanceHolder(parseAttributes(balanceNode)))));
   }
  
   public double getValueFor(ClassBalanceType type, Creature attacker, Creature target)
   {
       ClassBalanceHolder holder = _data.stream().filter(data -> data.getType() == type && data.getClassId().getId() == attacker.getActingPlayer().getClassId().getId() && data.getTargetId().getId() == target.getActingPlayer().getClassId().getId()).findFirst().orElse(null);
       return holder == null ? 1.0 : holder.getValue();
   }
  
   public List<ClassBalanceHolder> getData()
   {
       return _data;
   }
  
   public class ClassBalanceHolder
   {
       private ClassBalanceType _type;
       private ClassId _classId;
       private ClassId _targetId;
       private double _value;
      
       public ClassBalanceHolder(StatSet set)
       {
           _type = ClassBalanceType.valueOf(set.getString("type", "NORMAL"));
           _classId = ClassId.valueOf(set.getString("class"));
           _targetId = ClassId.valueOf(set.getString("target"));
           _value = set.getDouble("value", 1.0);
       }
      
       public ClassBalanceType getType()
       {
           return _type;
       }
      
       public ClassId getClassId()
       {
           return _classId;
       }
      
       public ClassId getTargetId()
       {
           return _targetId;
       }
      
       public double getValue()
       {
           return _value;
       }
   }
  
   public static ClassBalanceManager getInstance()
   {
       return SingletonHolder.INSTANCE;
   }
  
   private static class SingletonHolder
   {
       protected static final ClassBalanceManager INSTANCE = new ClassBalanceManager();
   }
}